import json
import math
import os
import unicodedata

# ------------------ CONFIGURAÇÕES ------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "rank_pingpong.json")

S = 200              # sensibilidade
K_NEW = 40           # Jogadores com poucas partidas
K_OLD = 20           # Jogadores Avançados
GAMES_THRESHOLD = 10 # Controle para iniciante

MIN_DELTA = 1
MAX_DELTA = 50

players = {}

# ------------------ FUNÇÕES AUXILIARES ------------------
def expectation(r_j: float, r_op: float) -> float:
    """Calcula expectativa de vitória do jogador com rating r_j contra r_op."""
    return 1 / (1 + 10 ** ((r_op - r_j) / S))

def save_data():
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(players, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print("Erro ao salvar dados:", e)

def load_data():
    global players
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                players = json.load(f)
            # garantir campos
            for name, info in players.items():
                info.setdefault("rating", 0)
                info.setdefault("games", 0)
                info.setdefault("rating_prev", 0)
        except Exception as e:
            print("Erro ao carregar, criando lista inicial:", e)
            players = {}

def show_ranking():
    if not players:
        print("\nNenhum jogador cadastrado.\n")
        return
    ranking = sorted(players.items(), key=lambda x: x[1]["rating"], reverse=True)
    print("\n===== Ranking Atual =====")
    for pos, (nome, info) in enumerate(ranking, 1):
        delta = info["rating_prev"]
        extra = f" (+{delta})" if delta > 0 else (f" ({delta})" if delta < 0 else "")
        print(f"{pos}. {nome} - {int(info['rating'])} rating{extra} (partidas: {info['games']})")
    print("=========================\n")

def add_player(name: str):
    if name in players:
        print("Jogador já existe.")
        return
    players[name] = {"rating": 0, "games": 0, "rating_prev": 0}
    save_data()
    print(f"Jogador '{name}' adicionado.")

def remove_player_by_index(index: int):
    names = sorted(players.keys())
    if 1 <= index <= len(names):
        nome = names[index - 1]
        del players[nome]
        save_data()
        print(f"Jogador '{nome}' removido.")
    else:
        print("Índice inválido.")

def select_player_by_number(prompt: str):
    names = sorted(players.keys())
    print("\nJogadores:")
    for i, n in enumerate(names, 1):
        print(f"{i}. {n} — {int(players[n]['rating'])} pts")
    while True:
        escolha = input(prompt).strip()
        if escolha.lower() in ("sair", "cancelar"):
            return None
        try:
            idx = int(escolha)
            if 1 <= idx <= len(names):
                return names[idx - 1]
            else:
                print("Número fora do intervalo.")
        except ValueError:
            print("Digite um número válido.")

def record_match(winner: str, loser: str):
    """Calcula o delta e armazena em rating_prev sem alterar rating real."""

    if players[winner]["games"] >= 5 or players[loser]["games"] >= 5:
        print("Um dos jogadores já realizou suas 5 partidas semanais. Resete o numero de partidas no inicio de cada semana.")
        return

    if winner == loser:
        print("Vencedor e perdedor não podem ser o mesmo.")
        return

    r_w, r_l = players[winner]["rating"], players[loser]["rating"]
    E_w = expectation(r_w, r_l)
    E_l = 1 - E_w

    K_w = K_NEW if players[winner]["games"] < GAMES_THRESHOLD else K_OLD
    K_l = K_NEW if players[loser]["games"] < GAMES_THRESHOLD else K_OLD

    delta_w = max(MIN_DELTA, min(MAX_DELTA, round(K_w * (1 - E_w))))
    delta_l = -max(MIN_DELTA, min(MAX_DELTA, round(K_l * (E_l)))) * 0.7

    players[winner]["rating_prev"] += delta_w
    players[loser]["rating_prev"] += delta_l
    players[winner]["games"] += 1
    players[loser]["games"] += 1

    print(f"\nPartida registrada: {winner} venceu {loser}.")

def atualizar_rating():
    """Aplica todos os rating_prev ao rating e zera os saldos."""
    for p in players.values():
        p["rating"] += p["rating_prev"]
        p["rating_prev"] = 0
    save_data()
    print("\nTodos os ratings foram atualizados!\n")

# ------------------ NOVAS FUNÇÕES ------------------
def resetar_games():
    for p in players.values():
        p["games"] = 0
    save_data()
    print("\nTodas as partidas foram resetadas! (pontuação mantida)\n")

def resetar_games_jogador(nome: str):
    if nome in players:
        players[nome]["games"] = 0
        save_data()
        print(f"Partidas de {nome} foram resetadas! (pontuação mantida)")
    else:
        print("Jogador não encontrado.")

# ------------------ MENU PRINCIPAL ------------------
def main_menu():
    load_data()
    while True:
        print("== Sistema de Rankeamento - Tênis de Mesa ==")
        print("1) Mostrar ranking")
        print("2) Registrar partida (vencedor / perdedor)")
        print("3) Adicionar jogador")
        print("4) Remover jogador")
        print("5) Atualizar ratings (aplicar saldos)")
        print("6) Resetar numero de partidas de todos os jogadores")
        print("7) Resetar numero partidas de um jogador")
        print("0) Sair")
        escolha = input("Escolha: ").strip()

        if escolha == "1":
            show_ranking()
        elif escolha == "2":
            v = select_player_by_number("Número do VENCEDOR: ")
            if not v:
                continue
            p = select_player_by_number("Número do PERDEDOR: ")
            if not p:
                continue
            record_match(v, p)
        elif escolha == "3":
            nome = input("Nome do novo jogador: ").strip()
            if nome:
                add_player(nome)
        elif escolha == "4":
            names = sorted(players.keys())
            for i, n in enumerate(names, 1):
                print(f"{i}. {n}")
            try:
                idx = int(input("Número do jogador a remover (ou 0 para cancelar): ").strip())
                if idx == 0:
                    continue
                remove_player_by_index(idx)
            except ValueError:
                print("Entrada inválida.")
        elif escolha == "5":
            atualizar_rating()
        elif escolha == "6":
            confirm = input("Digite SIM para confirmar reset de todas as partidas: ")
            if confirm == "SIM":
                resetar_games()
        elif escolha == "7":
            nome = select_player_by_number("Escolha o jogador: ")
            if nome:
                resetar_games_jogador(nome)
        elif escolha == "0":
            print("Saindo...")
            break
        else:
            print("Opção inválida.")

if __name__ == "__main__":
    main_menu()
