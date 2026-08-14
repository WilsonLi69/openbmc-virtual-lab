*** Settings ***
Documentation     Automated HIL testing for BMC power sequence using QEMU.
...               This suite verifies the Redfish Power On command and the 
...               corresponding CPLD hardware signal handshakes.
Library           qemu_simulation.library.bmc_qemu_library
Library           BuiltIn

# Suite Setup runs once before any test cases start
Suite Setup       Connect To QEMU Simulation    qmp_host=${IP}    qmp_port=${QMP_PORT}    redfish_host=${IP}    redfish_port=${REDFISH_PORT}  bmc_username=${USERNAME}    bmc_password=${PASSWORD}

# Suite Teardown runs once after all test cases finish, even if they fail
Suite Teardown    Disconnect From QEMU Simulation

*** Variables ***
${IP}             127.0.0.1
${QMP_PORT}       4444
${REDFISH_PORT}   2443
${USERNAME}       admin
${PASSWORD}       0penBmc

*** Test Cases ***
Ensure BMC Is Powered Off Before Test
    [Documentation]    Checks the initial power state and forces it Off if necessary to ensure a clean test environment.
    ${initial_state}=    Get Bmc Power State
    Run Keyword If    '${initial_state}' == 'On'    Reset BMC To Power Off

Verify BMC Power On Sequence With Virtual CPLD
    [Documentation]    Triggers Power On via Redfish, simulates CPLD hardware feedback (Power_Button -> PGOOD), and verifies the final state.
    
    # 1. Trigger the power on sequence via the software API
    Trigger Redfish Power On
    
    # 2. Let the Python library handle the low-level QMP GPIO polling and feedback
    Simulate Cpld Power Sequence    timeout=10.0
    
    # 3. Allow OpenBMC internal state managers to sync D-Bus properties
    Sleep    3s    Wait for BMC internal D-Bus state synchronization
    
    # 4. Verify the final outcome
    ${final_state}=    Get Bmc Power State
    Should Be Equal    ${final_state}    On    msg=CRITICAL: Expected PowerState to be 'On', but got '${final_state}'!

*** Keywords ***
Reset BMC To Power Off
    [Documentation]    Helper keyword to forcefully power off the BMC and wait for the state to settle.
    Trigger Redfish Power Off
    Sleep    5s    Wait for BMC to settle after ForceOff command
    ${state}=    Get Bmc Power State
    Should Be Equal    ${state}    Off    msg=Failed to force power off the BMC during setup!
