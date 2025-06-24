import hashlib
import json
import time
from uuid import uuid4
from urllib.parse import urlparse
import os

from flask import Flask, jsonify, request
import requests

CHAIN_DATA_DIR = "blockchain_data"


class ChatRageBlockchain:
    def __init__(self, node_id):
        self.node_id = node_id
        self.chain = []
        self.pending_transactions = []
        self.nodes = set()
        self.staked_balances = {}
        self.pending_rage_reports = {}
        self.data_file_path = os.path.join(CHAIN_DATA_DIR, f"chain_{node_id}.json")

        if self._load_chain_from_disk():
            print(f"[{self.node_id}] Блокчейн успешно загружен с диска. Длина цепи: {len(self.chain)}")
            self._recalculate_states_from_chain()
            print(f"[{self.node_id}] Состояния (балансы, отчеты) пересчитаны.")
        else:
            print(f"[{self.node_id}] Новый блокчейн инициализирован. Создание генезис-блока.")
            self.create_block(proof=1, previous_hash='1')

    def _save_chain_to_disk(self):
        os.makedirs(CHAIN_DATA_DIR, exist_ok=True)
        data_to_save = {
            'chain': self.chain,
            'pending_transactions': self.pending_transactions,
            'staked_balances': self.staked_balances,
            'pending_rage_reports': self.pending_rage_reports
        }
        with open(self.data_file_path, 'w') as f:
            json.dump(data_to_save, f, indent=4)
        print(f"[{self.node_id}] Блокчейн сохранен в {self.data_file_path}")

    def _load_chain_from_disk(self):
        if os.path.exists(self.data_file_path):
            try:  # НОВОЕ: Обработка ошибок при загрузке
                with open(self.data_file_path, 'r') as f:
                    data_loaded = json.load(f)
                    self.chain = data_loaded.get('chain', [])
                    self.pending_transactions = data_loaded.get('pending_transactions', [])
                    self.staked_balances = data_loaded.get('staked_balances', {})
                    self.pending_rage_reports = data_loaded.get('pending_rage_reports', {})
                # Простая проверка валидности загруженной цепочки
                if not self.chain or not self.valid_chain(self.chain):
                    print(f"[{self.node_id}] Загруженная цепочка невалидна или пуста. Инициализация новой.")
                    self.chain = []
                    return False
                return True
            except json.JSONDecodeError as e:
                print(f"[{self.node_id}] Ошибка при декодировании JSON из {self.data_file_path}: {e}")
                return False
        return False

    def create_block(self, proof, previous_hash=None):
        block = {
            'index': len(self.chain) + 1,
            'timestamp': time.time(),
            'transactions': self.pending_transactions,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1]),
        }
        self.pending_transactions = []
        self.chain.append(block)

        self._process_block_transactions(block['transactions'])
        self._save_chain_to_disk()

        return block

    def new_transaction(self, sender, recipient, amount, tx_type, data=None):
        transaction = {
            'sender': sender,
            'recipient': recipient,
            'amount': amount,
            'type': tx_type,
            'data': data
        }
        self.pending_transactions.append(transaction)
        # НОВОЕ: Более информативный вывод для транзакций
        print(f"[{self.node_id}] Новая транзакция типа '{tx_type}' от '{sender}' добавлена в ожидающие.")
        return self.last_block['index'] + 1

    @staticmethod
    def hash(block):
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    @property
    def last_block(self):
        return self.chain[-1]

    def proof_of_work(self, last_proof):
        proof = 0
        while self.valid_proof(last_proof, proof) is False:
            proof += 1
        return proof

    @staticmethod
    def valid_proof(last_proof, proof):
        guess = f'{last_proof}{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == "0000"

    def register_node(self, address):
        parsed_url = urlparse(address)
        if parsed_url.netloc:
            self.nodes.add(parsed_url.netloc)
            print(f"[{self.node_id}] Зарегистрирован новый узел: {parsed_url.netloc}")
        elif parsed_url.path:
            self.nodes.add(parsed_url.path)
            print(f"[{self.node_id}] Зарегистрирован новый узел: {parsed_url.path}")
        else:
            raise ValueError("Неверный URL узла")

    def valid_chain(self, chain):
        last_block = chain[0]
        current_index = 1
        while current_index < len(chain):
            block = chain[current_index]
            # НОВОЕ: Проверяем наличие всех обязательных полей
            if not all(k in block for k in ['index', 'timestamp', 'transactions', 'proof', 'previous_hash']):
                print(f"[{self.node_id}] DEBUG: Невалидный блок {block.get('index', 'N/A')}: отсутствуют поля.")
                return False
            if block['previous_hash'] != self.hash(last_block):
                print(f"[{self.node_id}] DEBUG: Невалидный блок {block['index']}: неверный previous_hash.")
                return False
            if not self.valid_proof(last_block['proof'], block['proof']):
                print(f"[{self.node_id}] DEBUG: Невалидный блок {block['index']}: неверный proof.")
                return False
            last_block = block
            current_index += 1
        return True

    def resolve_conflicts(self):
        neighbours = self.nodes
        new_chain = None
        max_length = len(self.chain)
        print(f"[{self.node_id}] Запуск разрешения конфликтов. Текущие узлы: {self.nodes}")

        for node in neighbours:
            try:
                print(f"[{self.node_id}] Запрашиваем цепочку у узла: {node}")
                response = requests.get(f'http://{node}/chain')
                if response.status_code == 200:
                    data = response.json()
                    length = data['length']
                    chain = data['chain']
                    print(f"[{self.node_id}] Получена цепочка длиной {length} от {node}.")
                    if length > max_length and self.valid_chain(chain):
                        max_length = length
                        new_chain = chain
                        print(f"[{self.node_id}] Обнаружена более длинная и валидная цепочка от {node}.")
            except requests.exceptions.ConnectionError:
                print(f"[{self.node_id}] Не удалось подключиться к узлу: {node}")
                continue
            except Exception as e:  # НОВОЕ: Общая обработка ошибок сети
                print(f"[{self.node_id}] Неизвестная ошибка при запросе к {node}: {e}")

        if new_chain:
            self.chain = new_chain
            self._recalculate_states_from_chain()
            self._save_chain_to_disk()
            print(f"[{self.node_id}] Цепочка была заменена более длинной и валидной.")
            return True
        print(f"[{self.node_id}] Наша цепочка является самой длинной и валидной.")
        return False

    def submit_rage_report(self, reporter_address, content_to_hash, reason_code, stake_amount=0):
        content_hash = hashlib.sha256(content_to_hash.encode()).hexdigest()

        report_data = {
            'report_id': str(uuid4()),
            'content_hash': content_hash,
            'reason_code': reason_code,
            'timestamp': time.time(),
            'reporter_address': reporter_address,
            'stake_amount': stake_amount
        }

        if stake_amount > 0:
            self.new_transaction(reporter_address, "RAGE_Staking_Pool", stake_amount, 'stake',
                                 data={'report_id': report_data['report_id']})

        return self.new_transaction(
            sender=reporter_address,
            recipient="Rage_Protocol",
            amount=0,
            tx_type='rage_report',
            data=report_data
        )

    def vote_on_rage_report(self, voter_address, report_id, vote_type):
        if vote_type not in ['approve', 'reject']:
            raise ValueError("Тип голоса должен быть 'approve' или 'reject'.")

        vote_data = {
            'report_id': report_id,
            'voter_address': voter_address,
            'vote_type': vote_type,
            'timestamp': time.time()
        }
        return self.new_transaction(
            sender=voter_address,
            recipient="Rage_DAO",
            amount=0,
            tx_type='vote_rage_report',
            data=vote_data
        )

    def get_rage_index(self, content_hash):
        rage_count = 0
        for block in self.chain:
            for tx in block['transactions']:
                if tx['type'] == 'rage_report' and tx['data']['content_hash'] == content_hash:
                    rage_count += 1
        return rage_count

    def _process_block_transactions(self, transactions):
        for tx in transactions:
            if tx['type'] == 'stake':
                sender = tx['sender']
                amount = tx['amount']
                self.staked_balances[sender] = self.staked_balances.get(sender, 0) + amount
                print(
                    f"[{self.node_id}] INFO: {sender} застейкал {amount} RAGE. Всего застейкано: {self.staked_balances[sender]}")  # DEBUG -> INFO
            elif tx['type'] == 'unstake':
                sender = tx['sender']
                amount = tx['amount']
                if self.staked_balances.get(sender, 0) >= amount:
                    self.staked_balances[sender] -= amount
                    print(
                        f"[{self.node_id}] INFO: {sender} анстейкал {amount} RAGE. Осталось застейкано: {self.staked_balances[sender]}")  # DEBUG -> INFO
                else:
                    print(
                        f"[{self.node_id}] WARN: {sender} пытается анстейкнуть больше, чем застейкано. Доступно: {self.staked_balances.get(sender, 0)}, Запрос: {amount}")  # DEBUG -> WARN
            elif tx['type'] == 'rage_report':
                report_id = tx['data']['report_id']
                self.pending_rage_reports[report_id] = {
                    'report_data': tx['data'],
                    'votes': {}
                }
                print(
                    f"[{self.node_id}] INFO: Rage Report {report_id} добавлен в ожидающие голосования.")  # DEBUG -> INFO

            elif tx['type'] == 'vote_rage_report':
                report_id = tx['data']['report_id']
                voter_address = tx['data']['voter_address']
                vote_type = tx['data']['vote_type']

                if report_id in self.pending_rage_reports:
                    if voter_address not in self.pending_rage_reports[report_id]['votes']:
                        self.pending_rage_reports[report_id]['votes'][voter_address] = vote_type
                        print(
                            f"[{self.node_id}] INFO: {voter_address} проголосовал '{vote_type}' за репорт {report_id}.")  # DEBUG -> INFO
                        self._check_and_reward_rage_report(report_id)
                    else:
                        print(
                            f"[{self.node_id}] WARN: {voter_address} уже голосовал за репорт {report_id}.")  # DEBUG -> WARN
                else:
                    print(
                        f"[{self.node_id}] WARN: Получено голосование за несуществующий или уже обработанный репорт {report_id}.")  # DEBUG -> WARN

            elif tx['type'] == 'transfer':
                print(
                    f"[{self.node_id}] INFO: Транзакция перевода: {tx['sender']} -> {tx['recipient']} Amount: {tx['amount']}")  # DEBUG -> INFO

    def _check_and_reward_rage_report(self, report_id):
        if report_id not in self.pending_rage_reports:
            return

        report_info = self.pending_rage_reports[report_id]

        approve_votes = sum(1 for vote_type in report_info['votes'].values() if vote_type == 'approve')
        reject_votes = sum(1 for vote_type in report_info['votes'].values() if vote_type == 'reject')

        if approve_votes >= 2 and reject_votes == 0:
            reporter = report_info['report_data']['reporter_address']
            reward_amount = 15

            self.new_transaction("Rage_Protocol_Reward", reporter, reward_amount, 'transfer')
            print(
                f"[{self.node_id}] SUCCESS: Rage Report {report_id} верифицирован! {reporter} получил {reward_amount} RAGE.")  # DEBUG -> SUCCESS

            del self.pending_rage_reports[report_id]
        elif reject_votes >= 2:
            reporter = report_info['report_data']['reporter_address']
            print(
                f"[{self.node_id}] INFO: Rage Report {report_id} отклонен! Возможно, штраф для {reporter}.")  # DEBUG -> INFO
            del self.pending_rage_reports[report_id]

    def _recalculate_states_from_chain(self):
        self.staked_balances = {}
        self.pending_rage_reports = {}
        for block in self.chain:
            for tx in block['transactions']:
                if tx['type'] == 'stake':
                    sender = tx['sender']
                    amount = tx['amount']
                    self.staked_balances[sender] = self.staked_balances.get(sender, 0) + amount
                elif tx['type'] == 'unstake':
                    sender = tx['sender']
                    amount = tx['amount']
                    if self.staked_balances.get(sender, 0) >= amount:
                        self.staked_balances[sender] -= amount
                elif tx['type'] == 'rage_report':
                    report_id = tx['data']['report_id']
                    self.pending_rage_reports[report_id] = {
                        'report_data': tx['data'],
                        'votes': {}
                    }
                elif tx['type'] == 'vote_rage_report':
                    report_id = tx['data']['report_id']
                    voter_address = tx['data']['voter_address']
                    vote_type = tx['data']['vote_type']
                    if report_id in self.pending_rage_reports and voter_address not in \
                            self.pending_rage_reports[report_id]['votes']:
                        self.pending_rage_reports[report_id]['votes'][voter_address] = vote_type

        reports_to_remove = []
        for report_id, info in self.pending_rage_reports.items():
            approve_votes = sum(1 for vote_type in info['votes'].values() if vote_type == 'approve')
            reject_votes = sum(1 for vote_type in info['votes'].values() if vote_type == 'reject')
            if (approve_votes >= 2 and reject_votes == 0) or reject_votes >= 2:
                reports_to_remove.append(report_id)

        for report_id in reports_to_remove:
            del self.pending_rage_reports[report_id]

    def get_staked_balance(self, address):
        return self.staked_balances.get(address, 0)

    def get_balance(self, address):
        balance = 0
        for block in self.chain:
            for tx in block['transactions']:
                if tx['type'] == 'transfer':
                    if tx['recipient'] == address:
                        balance += tx['amount']
                    if tx['sender'] == address:
                        balance -= tx['amount']
                elif tx['type'] == 'stake' and tx['sender'] == address:
                    balance -= tx['amount']
                elif tx['type'] == 'unstake' and tx['recipient'] == address:
                    # Анстейк увеличивает баланс, так как токены возвращаются
                    balance += tx['amount']
        return balance


app = Flask(__name__)
node_identifier = str(uuid4()).replace('-', '')
blockchain = ChatRageBlockchain(node_identifier)


@app.route('/mine', methods=['GET'])
def mine():
    last_block = blockchain.last_block
    last_proof = last_block['proof']
    proof = blockchain.proof_of_work(last_proof)

    blockchain.new_transaction(
        sender="0",
        recipient=node_identifier,
        amount=1,
        tx_type='transfer'
    )

    previous_hash = blockchain.hash(last_block)
    block = blockchain.create_block(proof, previous_hash)

    response = {
        'message': "Новый блок создан!",
        'index': block['index'],
        'transactions': block['transactions'],
        'proof': block['proof'],
        'previous_hash': block['previous_hash'],
        'node_id': node_identifier  # НОВОЕ: Добавляем ID узла в ответ майнинга
    }
    return jsonify(response), 200


@app.route('/transactions/new', methods=['POST'])
def new_transaction_api():
    values = request.get_json()
    required_fields = ['sender', 'type']
    if not all(field in values for field in required_fields):
        return 'Отсутствуют необходимые поля транзакции: sender, type', 400

    tx_type = values['type']
    sender = values['sender']
    recipient = values.get('recipient')
    amount = values.get('amount', 0)
    data = values.get('data')

    index = -1
    if tx_type == 'rage_report':
        required_rage_fields = ['content', 'reason_code']
        if not (data and all(field in data for field in required_rage_fields)):  # Убедимся, что data не None
            return 'Отсутствуют необходимые поля для Rage Report: content, reason_code', 400
        index = blockchain.submit_rage_report(
            sender,
            data['content'],
            data['reason_code'],
            data.get('stake_amount', 0)
        )
    elif tx_type == 'vote_rage_report':
        required_vote_fields = ['report_id', 'vote_type']
        if not (data and all(field in data for field in required_vote_fields)):  # Убедимся, что data не None
            return 'Отсутствуют необходимые поля для голосования: report_id, vote_type', 400
        index = blockchain.vote_on_rage_report(
            sender,
            data['report_id'],
            data['vote_type']
        )
    elif tx_type == 'transfer' or tx_type == 'stake' or tx_type == 'unstake':
        if not recipient or amount <= 0:
            return 'Для transfer/stake/unstake необходимы recipient и amount > 0', 400
        index = blockchain.new_transaction(sender, recipient, amount, tx_type, data)
    else:
        return 'Неизвестный тип транзакции', 400

    response = {'message': f'Транзакция будет добавлена в блок {index}'}
    return jsonify(response), 201


@app.route('/chain', methods=['GET'])
def full_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain),
        'node_id': node_identifier  # НОВОЕ: Добавляем ID узла
    }
    return jsonify(response), 200


@app.route('/nodes/register', methods=['POST'])
def register_nodes():
    values = request.get_json()
    nodes = values.get('nodes')
    if nodes is None:
        return "Пожалуйста, укажите список узлов", 400

    for node in nodes:
        blockchain.register_node(node)

    response = {
        'message': 'Новые узлы добавлены',
        'total_nodes': list(blockchain.nodes),
        'node_id': node_identifier  # НОВОЕ: Добавляем ID узла
    }
    return jsonify(response), 201


@app.route('/nodes/resolve', methods=['GET'])
def resolve_conflicts():
    replaced = blockchain.resolve_conflicts()

    if replaced:
        response = {
            'message': 'Наша цепочка была заменена',
            'new_chain': blockchain.chain,
            'node_id': node_identifier  # НОВОЕ: Добавляем ID узла
        }
    else:
        response = {
            'message': 'Наша цепочка является авторитетной',
            'chain': blockchain.chain,
            'node_id': node_identifier  # НОВОЕ: Добавляем ID узла
        }
    return jsonify(response), 200


@app.route('/balance/<address>', methods=['GET'])
def get_wallet_balance(address):
    balance = blockchain.get_balance(address)
    response = {
        'address': address,
        'balance': balance,
        'message': f'Баланс кошелька {address} составляет {balance} RAGE.',
        'node_id': node_identifier  # НОВОЕ: Добавляем ID узла
    }
    return jsonify(response), 200


@app.route('/staked_balance/<address>', methods=['GET'])
def get_wallet_staked_balance(address):
    staked_balance = blockchain.get_staked_balance(address)
    response = {
        'address': address,
        'staked_balance': staked_balance,
        'message': f'Застейкано {address}: {staked_balance} RAGE.',
        'node_id': node_identifier  # НОВОЕ: Добавляем ID узла
    }
    return jsonify(response), 200


@app.route('/rage_index', methods=['POST'])
def get_current_rage_index():
    values = request.get_json()
    content_to_hash = values.get('content')
    if not content_to_hash:
        return 'Необходимо указать "content" для хеширования', 400

    content_hash = hashlib.sha256(content_to_hash.encode()).hexdigest()
    rage_count = blockchain.get_rage_index(content_hash)

    response = {
        'content_hash': content_hash,
        'rage_index': rage_count,
        'message': f'Rage Index для данного контента: {rage_count}',
        'node_id': node_identifier  # НОВОЕ: Добавляем ID узла
    }
    return jsonify(response), 200


@app.route('/pending_rage_reports', methods=['GET'])
def get_pending_rage_reports():
    reports = []
    for report_id, info in blockchain.pending_rage_reports.items():
        report_data = info['report_data']
        votes = info['votes']
        reports.append({
            'report_id': report_id,
            'reporter_address': report_data['reporter_address'],
            'content_hash': report_data['content_hash'],
            'reason_code': report_data['reason_code'],
            'stake_amount': report_data['stake_amount'],
            'current_votes': votes
        })
    response = {
        'pending_reports': reports,
        'count': len(reports),
        'node_id': node_identifier  # НОВОЕ: Добавляем ID узла
    }
    return jsonify(response), 200


if __name__ == '__main__':
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=5000, type=int, help='порт для запуска узла')
    args = parser.parse_args()
    port = args.port

    app.run(host='0.0.0.0', port=port, debug=True)