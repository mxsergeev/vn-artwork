For every task in this repository, read [README.md](README.md) before starting work and follow its procedure throughout the task.

## Mandatory independent sprite/transplant review

Before declaring any new or transplanted sprite complete or publishing it, request a separate Codex subagent with **model `gpt-6-luna` and reasoning effort `xhigh`**. If that configuration is unavailable, do not mark the artwork complete; report that the required review could not be run.

Give the reviewer the exact candidate build identity and paths to the master/source, every donor used, final sprite or states, aligned donor, selection overlays, actual compositing stages, native-scale face comparison, and decoded animation frames when applicable. Include intended expression and display size. Do not give it the builder's pass/fail claims or explanation of why the result should be correct. It must open and visually inspect the images itself.

Require a **pass**, **fail**, or **uncertain** verdict for each candidate. The reviewer must assess naturalness and look for clipping, overflow, smearing, doubled or ghosted features, broken contours, mismatched joins, wrong expression states, and animation jumps. A clear visible defect is a fail; uncertain does not pass.

For every failure or uncertainty, the reviewer must provide:

- The image and stage where the problem first appears.
- Coordinates in the master canvas, with the coordinate frame stated.
- A separately saved, enlarged crop or image marked to point at the defect.
- A short description of what looks wrong and why.
- A proposed correction tied to the relevant technique in README.md, such as correcting landmark alignment, changing the patch boundary, repairing the old-feature background, restoring a complete intended strand, or rejecting an incompatible donor.

