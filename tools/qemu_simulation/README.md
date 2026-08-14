# OpenBMC Virtual Hardware-in-the-Loop (HIL) Automation Framework

## Overview

This project provides a fully automated, Headless Hardware-in-the-Loop (HIL) testing framework for OpenBMC firmware. By leveraging **QEMU** for AST2500 emulation and **Robot Framework** for test orchestration, it simulates hardware-level interactions (such as CPLD power sequence handshakes) without requiring physical server hardware. 

This framework is designed to be integrated into CI/CD pipelines (e.g., GitLab CI, GitHub Actions), ensuring that firmware modifications do not break critical hardware control logic before deployment.

## Scope & Capabilities

The automation framework is capable of handling the entire lifecycle of a BMC power control test:

1. **Environment Provisioning**: Dynamically spins up a headless QEMU instance running a custom Yocto-built OpenBMC ROM image (`evb-ast2500` based).
2. **Out-of-Band (OOB) Control**: Utilizes the `Redfish API` (via `bmcweb`) to issue remote power commands (e.g., Power On, Power Off, Reset) to the BMC.
3. **Low-Level Hardware Simulation**: A Python daemon acts as a virtual CPLD, communicating with QEMU via the **QEMU Machine Protocol (QMP)**. It monitors GPIO outputs (e.g., `Power_Button`) from the BMC and simulates the corresponding hardware feedback signals (e.g., pulling `PGOOD` high).
4. **Keyword-Driven Testing**: Test scenarios are written in human-readable Robot Framework syntax, decoupling high-level test logic from low-level communication protocols.
5. **CI/CD Ready**: Includes teardown and reporting mechanisms, producing standard HTML/XML test reports suitable for CI artifact storage.

---

## Architecture

The system is designed with a three-layer architecture to enforce the separation of concerns:

1. **Test Suite Layer (`*.robot`)**: Keyword-driven test specifications.
2. **Library Layer (`BmcQemuLibrary.py`)**: Robot Framework custom library that bridges test keywords to the underlying Python clients.
3. **Communication Layer (`QMPClient` & `RedfishClient`)**: Python modules handling socket-level QEMU communication and RESTful HTTP requests to the BMC.

---

## Project Roadmap & Progress Tracking

This roadmap outlines the implementation phases from the ground up.

### Phase 1: Core Python Control Libraries (Communication Layer)
- [ ] **1.1** Implement `QMPClient` class (Handle socket connection, JSON parsing, `qom-get`/`qom-set` for AST2500 GPIOs).
- [ ] **1.2** Implement `RedfishClient` class (Handle HTTPS requests, authentication, and payload formatting for BMC API).
- [ ] **1.3** Unit test Python classes locally against a running QEMU instance to verify stable connectivity and timeout handling.

### Phase 2: Robot Framework Custom Library (Library Layer)
- [ ] **2.1** Create `BmcQemuLibrary.py` wrapping the core Python clients.
- [ ] **2.2** Implement Hardware Simulation Logic (e.g., `Simulate Cpld Power Sequence` with polling loops and non-blocking timeout mechanisms).
- [ ] **2.3** Implement State Verification Logic (e.g., `Get Bmc Power State` for Robot Framework assertions).

### Phase 3: Robot Framework Test Suites (Test Layer)
- [ ] **3.1** Author `power_sequence.robot` including Suite Setup (provisioning) and Teardown.
- [ ] **3.2** Define specific Test Cases (e.g., Normal Power On Sequence, Power On Timeout Exception Handling).
- [ ] **3.3** Execute test scripts locally and validate HTML report generation.

### Phase 4: CI/CD Integration & Environment Scripting
- [ ] **4.1** Develop environment startup script (`start_qemu.sh`) with dynamic port allocation and headless execution (`-daemonize`).
- [ ] **4.2** Develop environment teardown script (`stop_qemu.sh`) for strict resource cleanup.
- [ ] **4.3** Author CI Pipeline Configuration (`.gitlab-ci.yml` or `.github/workflows/test.yml`) to orchestrate Yocto builds, test execution, and artifact archiving.

---

## Getting Started

