from uuid import uuid4
import requests
import json
import hashlib
import time

# Адрес узла, с которым будет взаимодействовать CLI
NODE_URL = "http://127.0.0.1:5000"
# Уникальный ID для нашего CLI-кошелька
CLI_WALLET_ADDRESS = str(uuid4()).replace('-', '')


def send_transaction(sender, recipient, amount, tx_type, data=None):
    """Отправляет общую транзакцию на узел."""
    payload = {
        "sender": sender,
        "recipient": recipient,
        "amount": amount,
        "type": tx_type,
        "data": data
    }
    headers = {'Content-Type': 'application/json'}
    try:
        response = requests.post(f"{NODE_URL}/transactions/new", data=json.dumps(payload), headers=headers)
        response.raise_for_status()  # Вызовет исключение для статусов 4xx/5xx
        print(f"Транзакция отправлена: {response.json().get('message')}")
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при отправке транзакции: {e}")
        if e.response:
            print(f"Ответ сервера: {e.response.json().get('message', e.response.text)}")


def mine_block():
    """Запрашивает майнинг нового блока у узла."""
    try:
        response = requests.get(f"{NODE_URL}/mine")
        response.raise_for_status()
        print(f"Майнинг... {response.json().get('message')}")
        print(f"Новый блок {response.json().get('index')} создан.")
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при майнинге: {e}")
        if e.response:
            print(f"Ответ сервера: {e.response.json().get('message', e.response.text)}")


def get_chain():
    """Получает всю цепочку блоков."""
    try:
        response = requests.get(f"{NODE_URL}/chain")
        response.raise_for_status()
        chain_info = response.json()
        print("\n--- ТЕКУЩАЯ ЦЕПОЧКА BLOCKCHAIN ---")
        print(f"Длина цепочки: {chain_info['length']}")
        for block in chain_info['chain']:
            print(f"Блок {block['index']}:")
            print(
                f"  Хеш: {block['previous_hash'][:10]}... -> {hashlib.sha256(json.dumps(block, sort_keys=True).encode()).hexdigest()[:10]}...")
            print(f"  Транзакции: {json.dumps(block['transactions'], indent=2)}")
        print("---------------------------------")
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при получении цепочки: {e}")


def get_balance(address=None):
    """Получает баланс кошелька."""
    address = address or CLI_WALLET_ADDRESS
    try:
        response = requests.get(f"{NODE_URL}/balance/{address}")
        response.raise_for_status()
        balance_info = response.json()
        print(f"Баланс кошелька {balance_info['address']}: {balance_info['balance']} RAGE.")
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при получении баланса: {e}")


def get_staked_balance(address=None):
    """Получает застейканный баланс кошелька."""
    address = address or CLI_WALLET_ADDRESS
    try:
        response = requests.get(f"{NODE_URL}/staked_balance/{address}")
        response.raise_for_status()
        balance_info = response.json()
        print(f"Застейкано кошелька {balance_info['address']}: {balance_info['staked_balance']} RAGE.")
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при получении застейканного баланса: {e}")


def submit_rage_report_cli():
    """Интерактивное создание Rage Report."""
    print("\n--- ОТПРАВИТЬ RAGE REPORT ---")
    content = input("Введите проблемный контент (например, ответ AI): ")
    reason_code = input("Причина Rage (например, TOXIC_AI_RESPONSE, MISINFORMATION): ")
    try:
        stake_amount = int(input("Сумма RAGE для стейкинга (0 для отсутствия): "))
    except ValueError:
        stake_amount = 0

    send_transaction(CLI_WALLET_ADDRESS, "Rage_Protocol", 0, 'rage_report', {
        "content": content,
        "reason_code": reason_code,
        "stake_amount": stake_amount
    })


def stake_cli():
    """Интерактивное стейкинг RAGE."""
    print("\n--- ЗАСТЕЙКАТЬ RAGE ---")
    try:
        amount = int(input("Введите сумму RAGE для стейкинга: "))
    except ValueError:
        print("Неверная сумма.")
        return
    if amount <= 0:
        print("Сумма должна быть больше нуля.")
        return
    send_transaction(CLI_WALLET_ADDRESS, "RAGE_Staking_Pool", amount, 'stake')


def unstake_cli():
    """Интерактивное анстейкинг RAGE."""
    print("\n--- АНСТЕЙКАТЬ RAGE ---")
    try:
        amount = int(input("Введите сумму RAGE для анстейкинга: "))
    except ValueError:
        print("Неверная сумма.")
        return
    if amount <= 0:
        print("Сумма должна быть больше нуля.")
        return
    send_transaction(CLI_WALLET_ADDRESS, "RAGE_Staking_Pool", amount, 'unstake')


def transfer_cli():
    """Интерактивная отправка RAGE."""
    print("\n--- ОТПРАВИТЬ RAGE ---")
    recipient = input("Адрес получателя: ")
    try:
        amount = int(input("Сумма RAGE для отправки: "))
    except ValueError:
        print("Неверная сумма.")
        return
    if amount <= 0:
        print("Сумма должна быть больше нуля.")
        return
    send_transaction(CLI_WALLET_ADDRESS, recipient, amount, 'transfer')


def get_pending_reports_cli():
    """Получает и отображает ожидающие голосования Rage Reports."""
    try:
        response = requests.get(f"{NODE_URL}/pending_rage_reports")
        response.raise_for_status()
        data = response.json()
        print("\n--- ОТЧЕТЫ RAGE, ОЖИДАЮЩИЕ ГОЛОСОВАНИЯ ---")
        if data['count'] == 0:
            print("Нет отчетов, ожидающих голосования.")
            return
        for report in data['pending_reports']:
            print(f"ID: {report['report_id']}")
            print(f"  Репортер: {report['reporter_address']}")
            print(f"  Хеш контента: {report['content_hash'][:20]}...")
            print(f"  Причина: {report['reason_code']}")
            print(f"  Застейкано: {report['stake_amount']} RAGE")
            print(f"  Голоса: {report['current_votes']}")
            print("-" * 30)
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при получении отчетов: {e}")


def vote_on_report_cli():
    """Интерактивное голосование за Rage Report."""
    get_pending_reports_cli()  # Показываем текущие отчеты
    report_id = input("\nВведите ID отчета, за который хотите проголосовать: ")
    vote_type = input("Ваш голос (approve/reject): ").lower()
    if vote_type not in ['approve', 'reject']:
        print("Неверный тип голоса. Используйте 'approve' или 'reject'.")
        return

    send_transaction(CLI_WALLET_ADDRESS, "Rage_DAO", 0, 'vote_rage_report', {
        "report_id": report_id,
        "vote_type": vote_type
    })


def main_menu():
    print(f"\n--- ChatRageCoin CLI (Кошелек: {CLI_WALLET_ADDRESS}) ---")
    print(f"Подключен к узлу: {NODE_URL}")
    print("1. Майнить новый блок")
    print("2. Отправить Rage Report")
    print("3. Проверить свой баланс RAGE")
    print("4. Проверить свой застейканный баланс RAGE")
    print("5. Застейкать RAGE")
    print("6. Анстейкать RAGE")
    print("7. Отправить RAGE другому кошельку")
    print("8. Показать всю цепочку")
    print("9. Показать отчеты RAGE, ожидающие голосования")
    print("10. Проголосовать за Rage Report")
    print("0. Выход")


def run_cli():
    while True:
        get_balance()  # Показываем текущий баланс при каждом запуске меню
        main_menu()
        choice = input("Выберите действие: ")

        if choice == '1':
            mine_block()
        elif choice == '2':
            submit_rage_report_cli()
        elif choice == '3':
            get_balance()
        elif choice == '4':
            get_staked_balance()
        elif choice == '5':
            stake_cli()
        elif choice == '6':
            unstake_cli()
        elif choice == '7':
            transfer_cli()
        elif choice == '8':
            get_chain()
        elif choice == '9':
            get_pending_reports_cli()
        elif choice == '10':
            vote_on_report_cli()
        elif choice == '0':
            print("Выход из ChatRageCoin CLI. Удачи!")
            break
        else:
            print("Неверный выбор. Пожалуйста, попробуйте еще раз.")

        # Небольшая пауза
        time.sleep(1)


if __name__ == '__main__':
    run_cli()