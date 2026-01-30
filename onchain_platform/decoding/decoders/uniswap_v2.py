from typing import Any, Dict, Iterable, List

from eth_abi import decode

from onchain_platform.decoding.abi_registry import ABIRegistry


def _topic_to_address(topic: str) -> str:
    if topic.startswith("0x"):
        topic = topic[2:]
    return "0x" + topic[-40:]


def decode_swaps(
    registry: ABIRegistry,
    logs: Iterable[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    event_abi = registry.get_event("uniswap_v2", "Swap")
    if not event_abi:
        raise RuntimeError("Uniswap V2 Swap ABI not found")
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
        if len(data) < 2 + 64 * 4:
            continue
        sender = _topic_to_address(topics[1])
        to_addr = _topic_to_address(topics[2])
        amount0_in, amount1_in, amount0_out, amount1_out = decode(
            ["uint256", "uint256", "uint256", "uint256"], bytes.fromhex(data[2:])
        )

        decoded.append(
            {
                "chain_id": log.get("chain_id"),
                "block_number": log.get("block_number"),
                "tx_hash": log.get("tx_hash"),
                "log_index": log.get("log_index"),
                "pair_address": log.get("address"),
                "sender": sender,
                "to_address": to_addr,
                "amount0_in": str(int(amount0_in)),
                "amount1_in": str(int(amount1_in)),
                "amount0_out": str(int(amount0_out)),
                "amount1_out": str(int(amount1_out)),
            }
        )

    return decoded
