from typing import Any, Dict, Iterable, List

from eth_abi import decode

from onchain_platform.decoding.abi_registry import ABIRegistry


TRANSFER_SIGNATURE = "Transfer(address,address,uint256)"


def _topic_to_address(topic: str) -> str:
    if topic.startswith("0x"):
        topic = topic[2:]
    return "0x" + topic[-40:]


def decode_transfers(
    registry: ABIRegistry,
    logs: Iterable[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    event_abi = registry.get_event("erc20", "Transfer")
    if not event_abi:
        raise RuntimeError("ERC20 Transfer ABI not found")
    topic0 = registry.event_topic(event_abi)

    decoded: List[Dict[str, Any]] = []
    for log in logs:
        topics = log.get("topics") or []
        if not topics:
            continue
        if topics[0].lower() != topic0.lower():
            continue
        if len(topics) < 3:
            continue
        data = log.get("data") or "0x"
        if len(data) < 66:
            continue
        from_addr = _topic_to_address(topics[1])
        to_addr = _topic_to_address(topics[2])
        value = decode(["uint256"], bytes.fromhex(data[2:]))[0]

        decoded.append(
            {
                "chain_id": log.get("chain_id"),
                "block_number": log.get("block_number"),
                "tx_hash": log.get("tx_hash"),
                "log_index": log.get("log_index"),
                "contract_address": log.get("address"),
                "from_address": from_addr,
                "to_address": to_addr,
                "value_raw": str(int(value)),
            }
        )

    return decoded
