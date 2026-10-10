"""VeriLoop checker.

Grades a Verilog design the model wrote. The checker is the authority: the model never overrides it.

    C1 (this part)  compile the design and explain any error in plain words, with the line
    C2              generate a test bench from the level's reference.py, simulate, compare
    C3              score 0-1 and feedback at three levels: A pass/fail, B how many wrong, C the first wrong step

Usage:
    python checker.py levels/03_counter design.v      # compile against the spec, simulate, compare
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


# ---------------------------------------------------------------- C2: simulate and compare

SIM_TIMEOUT_S = 10
TB = "__veriloop_tb"


@dataclass
class SimResult:
    compiled: CompileResult
    ran: bool = False            # the simulation finished and printed every step
    problem: str = ""            # why it did not run, in plain words (empty when it ran)
    rows: list = field(default_factory=list)        # per step: (inputs, expected, got)
    mismatches: list = field(default_factory=list)  # per wrong signal: dict(step, signal, expected, got)

    @property
    def passed(self):
        return self.compiled.ok and self.ran and not self.mismatches


def _mask(value, width):
    return int(value) & ((1 << width) - 1)


def testbench_source(ref, vecs):
    """A Verilog test bench that drives `vecs` into the design and prints every output after each step.

    Combinational: set the inputs, wait 1 ns, print. Clocked: set the inputs while clk is low, raise clk,
    print 1 ns after the rising edge (the contract: "the output just after that cycle's rising edge"),
    then lower clk. Outputs are printed in binary so an undefined value (x or z) shows up as such.
    """
    ins, outs = ref.INPUTS, ref.OUTPUTS
    L = ["`timescale 1ns/1ps", f"module {TB};"]
    if ref.CLOCKED:
        L.append("  reg clk;")
    L += [f"  reg {_decl(n, w)};" for n, w in ins.items()]
    L += [f"  wire {_decl(n, w)};" for n, w in outs.items()]
    conns = (["clk"] if ref.CLOCKED else []) + list(ins) + list(outs)
    L.append(f"  {ref.MODULE} dut(" + ", ".join(f".{n}({n})" for n in conns) + ");")
    fmt = " ".join(f"{n}=%b" for n in outs)
    show = f'$display("@@ %0d {fmt}", step, ' + ", ".join(outs) + ");"
    L += ["  integer step;", "  initial begin"]
    if ref.CLOCKED:
        L.append("    clk = 0;")
    for i, v in enumerate(vecs):
        sets = " ".join(f"{n} = {w}'d{_mask(v[n], w)};" for n, w in ins.items())
        if ref.CLOCKED:
            L.append(f"    step = {i}; {sets} #4 clk = 1; #1 {show} #5 clk = 0;")
        else:
            L.append(f"    step = {i}; {sets} #1 {show}")
    L += ["    $finish;", "  end", "endmodule"]
    return "\n".join(L) + "\n"


def _parse_bits(bits):
    return None if re.search(r"[xzXZ]", bits) else int(bits, 2)


def simulate(ref, design_src, workdir=None):
    """Compile the design against the spec, simulate it on ref.vectors(), and compare every output with
    ref.reference(). Returns a SimResult; C3 turns it into a score and feedback."""
    workdir = workdir or tempfile.mkdtemp(prefix="veriloop_")
    compiled = compile_verilog(design_src, ref.MODULE, ports_of(ref), workdir)
    result = SimResult(compiled)
    if not compiled.ok:
        return result

    vecs = ref.vectors()
    want = ref.reference(vecs)
    if len(want) != len(vecs):
        raise ValueError(f"reference() returned {len(want)} steps for {len(vecs)} vectors")

    tb = os.path.join(workdir, "tb.v")
    with open(tb, "w") as f:
        f.write(testbench_source(ref, vecs))
    sim = os.path.join(workdir, "tb_sim")
    p = subprocess.run([IVERILOG, "-g2012", "-s", TB, "-o", sim, tb, os.path.join(workdir, "design.v")],
                       capture_output=True, text=True, timeout=COMPILE_TIMEOUT_S)
    if p.returncode != 0:
        # The port probe passed, so this is rare; report it rather than guess.
        result.problem = "The design compiles alone but not inside the test bench: " + \
            (p.stdout + p.stderr).strip().splitlines()[0]
        return result

    try:
        run = subprocess.run(["vvp", "-n", sim], capture_output=True, text=True, timeout=SIM_TIMEOUT_S)
    except subprocess.TimeoutExpired:
        result.problem = (f"The simulation did not finish within {SIM_TIMEOUT_S}s. Usually a loop that never "
                          f"ends: a `while` or `for` inside an `always` block whose condition never becomes "
                          f"false, or logic whose output feeds back into its own input.")
        return result

    got_by_step = {}
    for line in run.stdout.splitlines():
        if line.startswith("@@ "):
            parts = line.split()
            got_by_step[int(parts[1])] = {k: _parse_bits(v) for k, v in (x.split("=", 1) for x in parts[2:])}
    if len(got_by_step) < len(vecs):
        result.problem = (f"The simulation stopped after {len(got_by_step)} of {len(vecs)} steps. Remove any "
                          f"`$finish`, `$stop` or `initial` block from the design -- the test bench drives it.")
        return result

    result.ran = True
    for i, (v, w) in enumerate(zip(vecs, want)):
        got = got_by_step[i]
        exp = {n: _mask(w[n], width) for n, width in ref.OUTPUTS.items()}
        result.rows.append((v, exp, got))
        for n in ref.OUTPUTS:
            if got.get(n) != exp[n]:
                result.mismatches.append(dict(step=i, signal=n, expected=exp[n], got=got.get(n)))
    return result


# ---------------------------------------------------------------- C3 goes below this line


def _show(value):
    return "x (undefined)" if value is None else str(value)


def _report_simulation(ref, design_src):
    """Plain report for people running the CLI. (The model's feedback levels A/B/C are C3's job.)"""
    r = simulate(ref, design_src)
    if not r.compiled.ok:
        print("DOES NOT COMPILE:")
        for m in r.compiled.messages:
            print(f"  - {m}")
        return 1
    if not r.ran:
        print(f"DID NOT RUN: {r.problem}")
        return 1
    steps = len(r.rows)
    if r.passed:
        print(f"PASS: all {steps} steps match the reference")
        return 0
    bad_steps = sorted({m["step"] for m in r.mismatches})
    print(f"FAIL: {len(bad_steps)} of {steps} steps wrong")
    for m in r.mismatches[:3]:
        inputs = r.rows[m["step"]][0]
        unit = "cycle" if ref.CLOCKED else "step"
        print(f"  - {unit} {m['step']}: inputs {inputs} -> `{m['signal']}` = {_show(m['got'])}, "
              f"expected {m['expected']}")
    return 1


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("paths", nargs="+", help="[LEVEL_DIR] DESIGN.v")
    ap.add_argument("--module", help="module name, when no level folder is given")
    a = ap.parse_args()

    if len(a.paths) == 2:
        ref = load_level(a.paths[0])
        if hasattr(ref, "vectors") and hasattr(ref, "reference"):
            return _report_simulation(ref, open(a.paths[1]).read())
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
