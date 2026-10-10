"""VeriLoop checker.

Grades a Verilog design the model wrote. The checker is the authority: the model never overrides it.

    C1 (this part)  compile the design and explain any error in plain words, with the line
    C2              generate a test bench from the level's reference.py, simulate, compare
    C3              score 0-1 and feedback at three levels: A pass/fail, B how many wrong, C the first wrong step

Usage:
    python checker.py levels/03_counter design.v      # compile against a level's spec (module name + ports)
    python checker.py design.v --module counter8      # compile only, no port check

Needs Icarus Verilog (`iverilog`) on the PATH -- see SERVER.md.
"""

import argparse
import importlib.util
import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field

IVERILOG = os.environ.get("IVERILOG", "iverilog")
COMPILE_TIMEOUT_S = 20
MAX_MESSAGES = 3          # more than this and the model fixes nothing; the first errors matter most
PROBE = "__veriloop_probe"


# ---------------------------------------------------------------- levels

def load_level(level_dir):
    """Load a level folder's reference.py (see levels/README.md for the contract)."""
    path = os.path.join(level_dir, "reference.py")
    if not os.path.isfile(path):
        raise FileNotFoundError(f"{level_dir} has no reference.py -- see levels/README.md")
    spec = importlib.util.spec_from_file_location("reference", path)
    ref = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ref)
    for name in ("MODULE", "INPUTS", "OUTPUTS", "CLOCKED"):
        if not hasattr(ref, name):
            raise ValueError(f"{path} is missing `{name}` -- see levels/README.md")
    return ref


def ports_of(ref):
    """The ports the spec promises: {name: (direction, width)}. A clocked level also gets `clk`."""
    ports = {}
    if ref.CLOCKED:
        ports["clk"] = ("input", 1)
    ports.update({n: ("input", w) for n, w in ref.INPUTS.items()})
    ports.update({n: ("output", w) for n, w in ref.OUTPUTS.items()})
    return ports


# ---------------------------------------------------------------- C1: compile

@dataclass
class CompileResult:
    ok: bool
    messages: list = field(default_factory=list)   # plain-words problems, for the model and for people
    raw: str = ""                                   # iverilog's own output, for debugging


def _decl(name, width):
    return f"[{width - 1}:0] {name}" if width > 1 else name


def _probe_source(module, ports):
    """A tiny wrapper that instantiates the design with the spec's port names and widths.

    Compiling it is how a wrong port name (an error) or a wrong width (only a warning in iverilog, which
    silently drops bits) gets caught before any simulation.
    """
    lines = [f"module {PROBE};"]
    for name, (direction, width) in ports.items():
        kind = "reg" if direction == "input" else "wire"
        lines.append(f"  {kind} {_decl(name, width)};")
    conns = ", ".join(f".{n}({n})" for n in ports)
    lines.append(f"  {module} dut({conns});")
    lines.append("endmodule")
    return "\n".join(lines) + "\n"


_LOC = re.compile(r"^(?P<file>[^:\n]+):(?P<line>\d+):\s*(?P<rest>.*)$")


def explain(raw, design_lines, module, ports):
    """Turn iverilog's output into at most MAX_MESSAGES plain-words messages, each naming the line.

    A verdict ("syntax error") is not an instruction. Each message says what is wrong AND what to change,
    without writing the design for the model.
    """
    out = []

    def src(n):
        return design_lines[n - 1].strip() if 0 < n <= len(design_lines) else ""

    def add(msg):
        if msg not in out:
            out.append(msg)

    port_list = ", ".join(f"{d} {_decl(n, w)}" for n, (d, w) in ports.items()) if ports else ""

    for line in raw.splitlines():
        m = _LOC.match(line)
        if not m:
            root = re.search(r'Unable to find the root module "([^"]+)"', line)
            if root:
                add(f"There is no module named `{module}`. The spec asks for exactly that name: "
                    f"`module {module}(...)`.")
            continue
        fname, n, rest = os.path.basename(m["file"]), int(m["line"]), m["rest"]
        in_design = fname == "design.v"

        if rest.startswith(":") or "Unable to elaborate" in rest:
            continue                       # continuation lines and knock-on errors add nothing

        if in_design and rest.startswith("syntax error"):
            text = src(n)
            if n == 1 and not re.match(r"\s*(module|`|//|/\*)", text):
                add(f"Line 1 is not Verilog: `{text[:80]}`. Send only the Verilog module -- no words "
                    f"before or after it.")
                continue
            hint = "The mistake is often at the end of the line just before it -- a missing `;`."
            src_all = "\n".join(design_lines)
            begins = len(re.findall(r"\bbegin\b", src_all))
            ends = len(re.findall(r"\bend\b", src_all))
            if begins > ends:
                hint = (f"There are {begins} `begin` but only {ends} `end`: a block is not closed "
                        f"before this line.")
            add(f"Syntax error at line {n}: `{text[:80]}`. {hint}")
            continue

        x = re.search(r"Unable to bind wire/reg/memory `([^']+)'", rest)
        if x:
            add(f"Line {n}: `{src(n)[:80]}` uses `{x[1]}`, which is never declared. Declare it, or use "
                f"a port name from the spec.")
            continue
        # iverilog 13: "'count' is not a valid l-value for a procedural assignment"
        # iverilog 12: "count is not a valid l-value in top.dut."
        x = re.search(r"'?([A-Za-z_]\w*)'? is not a valid l-value", rest)
        if x:
            add(f"Line {n}: `{x[1]}` is assigned inside an `always` block but declared as a wire. "
                f"Declare it as `reg` -- for an output port, `output reg {x[1]}` with its width.")
            continue
        x = re.search(r"'([^']+)' has already been declared", rest)
        if x:
            add(f"Line {n}: `{x[1]}` is declared twice. Keep only one declaration.")
            continue
        x = re.search(r"Unknown module type: (\S+)", rest)
        if x and not in_design and x[1] == module:
            # Raised by the port probe: the design never defines the module the spec names.
            add(f"There is no module named `{module}`. The spec asks for exactly that name: "
                f"`module {module}(...)`.")
            continue
        if x:
            add(f"Line {n}: the design uses a module `{x[1]}` that is not defined. Put everything inside "
                f"the one module `{module}`, or define `{x[1]}` in the same file.")
            continue
        x = re.search(r"port ``([^']+)'' is not a port of", rest)
        if x:
            add(f"The module has no port named `{x[1]}`. The spec's ports are exactly: {port_list}. "
                f"Use those names.")
            continue
        # iverilog 13: "Port 1 (a) of module add4 expects 3 bit(s), given 4."
        # iverilog 12: "Port 1 (a) of add4 expects 3 bits, got 4."
        x = re.search(r"Port \d+ \(([^)]+)\) of (?:module )?\S+ expects (\d+) bits?(?:\(s\))?, "
                      r"(?:given|got) (\d+)", rest)
        if x:
            name, got, want = x[1], int(x[2]), int(x[3])
            add(f"Port `{name}` is {got} bit(s) wide, but the spec says {want}. Declare it as "
                f"`{_decl(name, want)}`.")
            continue
        if "error" in rest:
            where = f"Line {n}: `{src(n)[:80]}` -- " if in_design else ""
            add(f"{where}{rest.replace('error: ', '')}")

        if len(out) >= MAX_MESSAGES:
            break

    if not out and raw.strip():
        out.append("The design does not compile: " + raw.strip().splitlines()[0])
    return out[:MAX_MESSAGES]


def compile_verilog(design_src, module, ports=None, workdir=None):
    """Compile `design_src` (Verilog text). With `ports`, also check the module has exactly the spec's
    port names and widths. Returns a CompileResult; on success `workdir` holds the compiled `sim`."""
    if not shutil.which(IVERILOG):
        raise RuntimeError("iverilog is not installed here -- see SERVER.md, 'Install the simulator'.")
    workdir = workdir or tempfile.mkdtemp(prefix="veriloop_")
    design = os.path.join(workdir, "design.v")
    with open(design, "w") as f:
        f.write(design_src)

    files, top = [design], module
    if ports:
        probe = os.path.join(workdir, "probe.v")
        with open(probe, "w") as f:
            f.write(_probe_source(module, ports))
        files, top = [probe, design], PROBE

    # -g2012 accepts the SystemVerilog style the model often writes (logic, always_ff, '0).
    cmd = [IVERILOG, "-g2012", "-s", top, "-o", os.path.join(workdir, "sim")] + files
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=COMPILE_TIMEOUT_S)
    except subprocess.TimeoutExpired:
        return CompileResult(False, [f"Compiling took over {COMPILE_TIMEOUT_S}s -- the design is "
                                     f"probably far too large or loops forever at compile time."])
    raw = (p.stdout + p.stderr).strip()
    messages = explain(raw, design_src.splitlines(), module, ports)
    width_problem = any(m.startswith("Port `") and "bit(s) wide" in m for m in messages)  # a warning in iverilog
    ok = p.returncode == 0 and not width_problem
    return CompileResult(ok, [] if ok else messages, raw)


# ---------------------------------------------------------------- C2 / C3 go below this line


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("paths", nargs="+", help="[LEVEL_DIR] DESIGN.v")
    ap.add_argument("--module", help="module name, when no level folder is given")
    a = ap.parse_args()

    if len(a.paths) == 2:
        ref = load_level(a.paths[0])
        module, ports, design_path = ref.MODULE, ports_of(ref), a.paths[1]
    else:
        if not a.module:
            ap.error("give a level folder, or --module NAME")
        module, ports, design_path = a.module, None, a.paths[0]

    r = compile_verilog(open(design_path).read(), module, ports)
    if r.ok:
        print(f"COMPILES: `{module}`" + (" with the spec's ports" if ports else ""))
        return 0
    print("DOES NOT COMPILE:")
    for m in r.messages:
        print(f"  - {m}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
