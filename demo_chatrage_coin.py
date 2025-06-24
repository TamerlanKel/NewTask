import time
import requests
import json
import os
import hashlib
from chatrage_coin import CHAIN_DATA_DIR

# Конфигурация демонстрации
NODE_PORTS = [5000, 5001]  # Порты для наших узлов
NODE_URLS = [f"http://127.0.0.1:{p}" for p in NODE_PORTS]
ALICE_WALLET = "alice_wallet_address"
BOB_WALLET = "bob_wallet_address"
BAD_CONTENT_HASH = hashlib.sha256("Этот ИИ-бот постоянно генерирует бессмысленный код.".encode()).hexdigest()


# Вспомогательные функции для HTTP-запросов
def send_get_request(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Ошибка GET-запроса к {url}: {e}")
        if e.response: print(f"Ответ сервера: {e.response.json().get('message', e.response.text)}")
        return None


def send_post_request(url, payload):
    headers = {'Content-Type': 'application/json'}
    try:
        response = requests.post(url, data=json.dumps(payload), headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Ошибка POST-запроса к {url} с payload {payload}: {e}")
        if e.response: print(f"Ответ сервера: {e.response.json().get('message', e.response.text)}")
        return None


def mine_block_on_node(node_url):
    print(f"\n[DEMO] Майним блок на {node_url}...")
    return send_get_request(f"{node_url}/mine")


def get_balance_on_node(node_url, address):
    print(f"[DEMO] Проверяем баланс {address} на {node_url}...")
    return send_get_request(f"{node_url}/balance/{address}")


def get_staked_balance_on_node(node_url, address):
    print(f"[DEMO] Проверяем застейканный баланс {address} на {node_url}...")
    return send_get_request(f"{node_url}/staked_balance/{address}")


def register_nodes(source_node_url, target_node_urls):
    print(f"\n[DEMO] Регистрируем узлы {target_node_urls} на {source_node_url}...")
    payload = {"nodes": target_node_urls}
    return send_post_request(f"{source_node_url}/nodes/register", payload)


def resolve_conflicts_on_node(node_url):
    print(f"\n[DEMO] Разрешаем конфликты на {node_url}...")
    return send_get_request(f"{node_url}/nodes/resolve")


def submit_rage_report(node_url, sender, content, reason_code, stake_amount=0):
    print(f"\n[DEMO] {sender} отправляет Rage Report на {node_url}...")
    payload = {
        "sender": sender,
        "recipient": "Rage_Protocol",
        "amount": 0,
        "type": "rage_report",
        "data": {
            "content": content,
            "reason_code": reason_code,
            "stake_amount": stake_amount
        }
    }
    return send_post_request(f"{node_url}/transactions/new", payload)


def vote_on_rage_report(node_url, voter, report_id, vote_type):
    print(f"\n[DEMO] {voter} голосует '{vote_type}' за report {report_id[:8]}... на {node_url}...")
    payload = {
        "sender": voter,
        "recipient": "Rage_DAO",
        "amount": 0,
        "type": "vote_rage_report",
        "data": {
            "report_id": report_id,
            "vote_type": vote_type
        }
    }
    return send_post_request(f"{node_url}/transactions/new", payload)


def transfer_funds(node_url, sender, recipient, amount):
    print(f"\n[DEMO] {sender} переводит {amount} RAGE {recipient} на {node_url}...")
    payload = {
        "sender": sender,
        "recipient": recipient,
        "amount": amount,
        "type": "transfer"
    }
    return send_post_request(f"{node_url}/transactions/new", payload)


def get_pending_reports(node_url):
    print(f"\n[DEMO] Запрашиваем ожидающие Rage Reports на {node_url}...")
    return send_get_request(f"{node_url}/pending_rage_reports")


# Основной сценарий демонстрации
def run_demo():
    print("--- ЗАПУСК ДЕМОНСТРАЦИИ CHATRAGECOIN ---")
    print("Убедитесь, что узлы Flask запущены на портах:", NODE_PORTS)
    time.sleep(5)  # Даем узлам время на старт

    # Шаг 1: Подготовка узлов и получение начальных RAGE
    print("\n[ШАГ 1] Подготовка: Майним несколько блоков на Узле 1 и получаем ID узлов.")
    node_1_id = send_get_request(f"{NODE_URLS[0]}/mine")['transactions'][0][
        'recipient']  # Майнинг дает награду узлу, берем его ID
    mine_block_on_node(NODE_URLS[0])
    mine_block_on_node(NODE_URLS[0])
    print(f"ID Узла 1: {node_1_id}")
    time.sleep(1)

    print("\n[ШАГ 1] Переводим средства Alice и Bob.")
    transfer_funds(NODE_URLS[0], node_1_id, ALICE_WALLET, 20)
    transfer_funds(NODE_URLS[0], node_1_id, BOB_WALLET, 15)
    mine_block_on_node(NODE_URLS[0])  # Включаем переводы в блок

    get_balance_on_node(NODE_URLS[0], ALICE_WALLET)
    get_balance_on_node(NODE_URLS[0], BOB_WALLET)
    time.sleep(2)

    # Rage Report со стейком от Alice
    print("\n[ШАГ 2] Alice отправляет Rage Report с 5 RAGE.")
    content_alice = "Этот ИИ-бот постоянно генерирует бессмысленный код."
    report_alice = submit_rage_report(NODE_URLS[0], ALICE_WALLET, content_alice, "IRRELEVANT_AI_RESPONSE", 5)
    mine_block_on_node(NODE_URLS[0])
    get_balance_on_node(NODE_URLS[0], ALICE_WALLET)
    get_staked_balance_on_node(NODE_URLS[0], ALICE_WALLET)

    pending_reports = get_pending_reports(NODE_URLS[0])
    report_id_alice = None
    if pending_reports and pending_reports['count'] > 0:
        report_id_alice = pending_reports['pending_reports'][0]['report_id']
        print(f"ID отчета Alice: {report_id_alice}")
    time.sleep(2)

    # Bob голосует 'approve' за отчет Alice
    print("\n[ШАГ 3] Bob голосует 'approve' за отчет Alice.")
    if report_id_alice:
        vote_on_rage_report(NODE_URLS[0], BOB_WALLET, report_id_alice, 'approve')
        mine_block_on_node(NODE_URLS[0])
    time.sleep(2)

    # Регистрируем Узел 2 и синхронизируем
    print("\n[ШАГ 4] Регистрируем Узел 2 на Узле 1 и разрешаем конфликты на Узле 2.")
    register_nodes(NODE_URLS[0], [NODE_URLS[1]])  # Узел 1 знает про Узел 2
    time.sleep(1)
    register_nodes(NODE_URLS[1], [NODE_URLS[0]])  # Узел 2 знает про Узел 1

    resolve_conflicts_on_node(NODE_URLS[1])  # Узел 2 синхронизируется с Узлом 1

    # Проверяем, что цепочки совпадают
    chain_node1 = send_get_request(f"{NODE_URLS[0]}/chain")
    chain_node2 = send_get_request(f"{NODE_URLS[1]}/chain")
    if chain_node1 and chain_node2 and len(chain_node1['chain']) == len(chain_node2['chain']):
        print("[DEMO] Узлы синхронизированы успешно!")
    else:
        print("[DEMO] Ошибка синхронизации узлов.")
    time.sleep(2)

    # Третий голос (например, от Alice еще раз, или нового кошелька)
    print("\n[ШАГ 5] Alice голосует 'approve' за свой отчет (второй голос).")
    if report_id_alice:
        vote_on_rage_report(NODE_URLS[0], ALICE_WALLET, report_id_alice, 'approve')
        mine_block_on_node(NODE_URLS[0])  # Этот майнинг должен активировать награду
        print("[DEMO] Проверяем логи Узла 1 - должна быть награда для Alice.")
    time.sleep(2)

    # Проверка наград и очистка pending reports
    print("\n[ШАГ 6] Проверяем баланс Alice и список ожидающих репортов.")
    get_balance_on_node(NODE_URLS[0], ALICE_WALLET)
    get_staked_balance_on_node(NODE_URLS[0], ALICE_WALLET)  # Стейк остается
    get_pending_reports(NODE_URLS[0])  # Отчет Alice должен исчезнуть

    print("\n--- ДЕМОНСТРАЦИЯ CHATRAGECOIN ЗАВЕРШЕНА ---")


if __name__ == "__main__":
    import hashlib  # Необходимо для BAD_CONTENT_HASH

    # Создаем папку для данных блокчейна, если ее нет
    os.makedirs(CHAIN_DATA_DIR, exist_ok=True)
    run_demo()