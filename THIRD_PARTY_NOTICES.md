# Third-party notices

This repository contains or depends on third-party material. The TerraRover-Gen project license does not replace the licenses of those components.

## Clearpath Husky description assets

`UnityProject/Assets/Robots/Husky/husky_description/` contains Husky URDF/xacro and mesh assets originating from the Clearpath Robotics Husky description. The archived `husky.urdf`, `husky.urdf.xacro`, and related xacro sources carry the following BSD 3-Clause terms from Clearpath Robotics:

> Copyright (c) 2015, Clearpath Robotics, Inc. All rights reserved.
>
> Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:
>
> 1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
> 2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.
> 3. Neither the name of Clearpath Robotics nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.
>
> THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

Some related Husky xacro files in the archived source carry later Clearpath copyright years while retaining the same BSD terms; those embedded notices are preserved unchanged.

## Unity packages

Unity ML-Agents and Unity Robotics URDF Importer are not vendored into this repository. `UnityProject/Packages/manifest.json` references the official package sources/versions used to reconstruct the project. Their own upstream licenses apply.

## Verification before release

This notice records the third-party material identified during the repository audit. Before a public release, the authors should perform one final license review if any additional asset is added to `UnityProject/Assets/`.
