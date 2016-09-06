import pytest

from eth_abi import (
    encode_abi,
)
from web3.utils.string import (
    force_obj_to_bytes,
)
from web3.utils.abi import (
    get_abi_input_types,
    function_abi_to_4byte_selector,
)
from web3.utils.encoding import (
    decode_hex,
)


@pytest.fixture
def FutureBlockCall(chain):
    return chain.get_contract_factory('FutureBlockCall')


@pytest.fixture
def Canary(chain):
    return chain.get_contract_factory('Canary')


@pytest.fixture
def CallLib(chain):
    return chain.get_contract_factory('CallLib')


@pytest.fixture
def SchedulerLib(chain):
    return chain.get_contract_factory('SchedulerLib')


def get_block_gas_limit(web3):
    latest_block = web3.eth.getBlock('latest')
    return latest_block['gasLimit']


@pytest.fixture
def deploy_fbc(chain, web3, FutureBlockCall):

    def _deploy_fbc(contract=None,
                    method_name=None,
                    arguments=None,
                    scheduler_address=None,
                    target_block=None,
                    grace_period=255,
                    required_gas=1000000,
                    payment=1,
                    donation=1,
                    endowment=None,
                    call_data="",
                    require_depth=0,
                    call_value=0):
        if arguments is not None and call_data:
            raise ValueError("Cannot specify both arguments and call_data")
        elif arguments is not None and not method_name:
            raise ValueError("Method name must be provided if providing arguments")

        if endowment is None:
            endowment = (
                get_block_gas_limit(web3) *
                web3.eth.gasPrice +
                payment +
                donation +
                call_value
            )

        if target_block is None:
            target_block = web3.eth.blockNumber

        if scheduler_address is None:
            scheduler_address = web3.eth.coinbase

        if contract is None:
            contract_address = web3.eth.coinbase
        else:
            contract_address = contract.address

        if method_name is None:
            abi_signature = ""
        else:
            method_abi = contract.find_matching_fn_abi('setBool', arguments)
            hex_abi_signature = function_abi_to_4byte_selector(method_abi)
            abi_signature = decode_hex(hex_abi_signature)

            if not call_data and arguments:
                arguent_types = get_abi_input_types(method_abi)
                call_data = encode_abi(
                    arguent_types,
                    force_obj_to_bytes(arguments),
                )

        deploy_txn_hash = FutureBlockCall.deploy(
            {'value': endowment},
            [
                scheduler_address,
                target_block,
                grace_period,
                contract_address,
                abi_signature,
                call_data,
                call_value,
                required_gas,
                require_depth,
                payment,
                donation,
            ],
        )

        contract_address = chain.wait.for_contract_address(deploy_txn_hash)
        fbc = FutureBlockCall(address=contract_address)
        return fbc
    return _deploy_fbc


#
# TODO: rework this.
#
#@pytest.fixture()
#def deploy_canary_contract(deployed_contracts, deploy_client, denoms, Canary):
#    from populus.contracts import (
#        deploy_contract,
#    )
#    from populus.utils import (
#        get_contract_address_from_txn,
#    )
#    def _deploy_canary_contract(endowment=None, scheduler_address=None):
#        if endowment is None:
#            endowment = 5 * denoms.ether
#
#        if scheduler_address is None:
#            scheduler_address = deployed_contracts.Scheduler._meta.address
#
#        deploy_txn_hash = deploy_contract(
#            deploy_client,
#            Canary,
#            constructor_args=(scheduler_address,),
#            gas=int(deploy_client.get_max_gas() * 0.95),
#            value=endowment,
#        )
#
#        canary_address = get_contract_address_from_txn(deploy_client, deploy_txn_hash, 180)
#        canary = Canary(canary_address, deploy_client)
#        return canary
#    return _deploy_canary_contract
#
#
#@pytest.fixture()
#def canary(deploy_canary_contract):
#    return deploy_canary_contract()
#
#
#@pytest.fixture(scope="module")
#def get_call(SchedulerLib, FutureBlockCall, deploy_client):
#    def _get_call(txn_hash):
#        call_scheduled_logs = SchedulerLib.CallScheduled.get_transaction_logs(txn_hash)
#        if not len(call_scheduled_logs):
#            call_rejected_logs = SchedulerLib.CallRejected.get_transaction_logs(txn_hash)
#            if len(call_rejected_logs):
#                reject_data = SchedulerLib.CallRejected.get_log_data(call_rejected_logs[0])
#                raise ValueError("CallRejected: {0}".format(reject_data))
#            raise ValueError("No scheduled call found")
#        call_scheduled_data = SchedulerLib.CallScheduled.get_log_data(call_scheduled_logs[0])
#
#        call_address = call_scheduled_data['call_address']
#        call = FutureBlockCall(call_address, deploy_client)
#        return call
#    return _get_call
#
#
#@pytest.fixture(scope="module")
#def get_call_rejection_data(SchedulerLib):
#    def _get_rejection_data(txn_hash):
#        rejection_logs = SchedulerLib.CallRejected.get_transaction_logs(txn_hash)
#        assert len(rejection_logs) == 1
#        rejection_data = SchedulerLib.CallRejected.get_log_data(rejection_logs[0])
#
#        return rejection_data
#    return _get_rejection_data
#
#
#@pytest.fixture(scope="module")
#def get_execution_data(CallLib):
#    def _get_execution_data(txn_hash):
#        execution_logs = CallLib.CallExecuted.get_transaction_logs(txn_hash)
#        assert len(execution_logs) == 1
#        execution_data = CallLib.CallExecuted.get_log_data(execution_logs[0])
#
#        return execution_data
#    return _get_execution_data

@pytest.fixture()
def denoms():
    from web3.utils.currency import units
    int_units = {
        key: int(value)
        for key, value in units.items()
    }
    return type('denoms', (object,), int_units)
