from pygame import *
import socket
import json
from threading import Thread

# ---ПУГАМЕ НАЛАШТУВАННЯ ---
WIDTH, HEIGHT = 800, 600
init()
mixer.init()
screen = display.set_mode((WIDTH, HEIGHT))
clock = time.Clock()
display.set_caption("Пінг-Понг")

# ---СЕРВЕР ---
def connect_to_server():
    while True:
        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect(('localhost', 8080)) # ---- Підключення до сервера
            buffer = ""
            game_state = {}
            my_id = int(client.recv(24).decode())
            return my_id, game_state, buffer, client
        except:
            pass


def receive():
    global buffer, game_state, game_over
    while not game_over:
        try:
            data = client.recv(1024).decode()
            buffer += data
            while "\n" in buffer:
                packet, buffer = buffer.split("\n", 1)
                if packet.strip():
                    game_state = json.loads(packet)
        except:
            game_state["winner"] = -1
            break

# --- ШРИФТИ ---
font_win = font.Font(None, 72)
font_main = font.Font(None, 36)

# --- ЗОБРАЖЕННЯ ----
try:
    fon = image.load('fon.jpg').convert()
    fon = transform.scale(fon, (WIDTH, HEIGHT))
except:
    fon = Surface((WIDTH, HEIGHT))
    fon.fill((30, 30, 30))

# --- ЗВУКИ ---
try:
    wall_sound = mixer.Sound('ball.mp3')
    print('- ball.mp3 loaded')

    platform_sound = mixer.Sound('ball.mp3')
    print('- platform sound loaded')

    win_sound = mixer.Sound('win.mp3')
    print('- win.mp3 loaded')

    lose_sound = mixer.Sound('lose.mp3')
    print('- lose.mp3 loaded')

    mixer.music.load('background.mp3')
    print('- background.mp3 loaded')

    mixer.music.set_volume(0.6)
    mixer.music.play(-1)
    print("Фонова музика запущена в циклі")
except Exception as e:
    print("ПОМИЛКА ПРИ ЗАВАНТАЖЕННІ ЗВУКУ, ПОПЕРЕДЖЕННЯ", e)

# --- ГРА ---
game_over = False
winner = None
you_winner = None
my_id, game_state, buffer, client = connect_to_server()
Thread(target=receive, daemon=True).start()

sound_played = False  # Щоб звук перемоги/поразки грав лише один раз

while True:
    for e in event.get():
        if e.type == QUIT:
            exit()

    if "countdown" in game_state and game_state["countdown"] > 0:
        screen.blit(fon, (0, 0))
        countdown_text = font.Font(None, 72).render(str(game_state["countdown"]), True, (255, 255, 255))
        screen.blit(countdown_text, (WIDTH // 2 - 20, HEIGHT // 2 - 30))
        display.update()
        continue  # Не малюємо гру до завершення відліку

    if "winner" in game_state and game_state["winner"] is not None:
        screen.blit(fon, (0, 0))

        if you_winner is None:  # Встановлюємо тільки один раз
            if game_state["winner"] == my_id:
                you_winner = True
            else:
                you_winner = False

        # Відтворення звуку перемоги/поразки
        if not sound_played:
            try:
                mixer.music.stop()
                if you_winner:
                    win_sound.play()
                else:
                    lose_sound.play()
            except:
                pass
            sound_played = True

        if you_winner:
            text = "Ти переміг!"
        else:
            text = "Пощастить наступним разом!"

        win_text = font_win.render(text, True, (255, 215, 0))
        text_rect = win_text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
        screen.blit(win_text, text_rect)

        text = font_win.render('К - рестарт', True, (255, 215, 0))
        text_rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 120))
        screen.blit(text, text_rect)

        display.update()
        continue  # Блокує гру після перемоги

    if game_state:
        # Малюємо фон замість однотонної заливки
        screen.blit(fon, (0, 0))
        
        draw.rect(screen, (0, 255, 0), (20, game_state['paddles']['0'], 20, 100))
        draw.rect(screen, (255, 0, 255), (WIDTH - 40, game_state['paddles']['1'], 20, 100))
        draw.circle(screen, (255, 255, 255), (game_state['ball']['x'], game_state['ball']['y']), 10)
        score_text = font_main.render(f"{game_state['scores'][0]} : {game_state['scores'][1]}", True, (255, 255, 255))
        screen.blit(score_text, (WIDTH // 2 - 25, 20))

        # Обробка звукових подій від сервера
        if game_state.get('sound_event'):
            event_type = game_state['sound_event']
            try:
                if event_type == 'wall_hit':
                    wall_sound.play()
                elif event_type == 'platform_hit':
                    platform_sound.play()
            except:
                pass
    else:
        screen.blit(fon, (0, 0))
        wating_text = font_main.render(f"Очікування гравців...", True, (255, 255, 255))
        screen.blit(wating_text, (WIDTH // 2 - 100, HEIGHT // 2))

    display.update()
    clock.tick(60)

    keys = key.get_pressed()
    if keys[K_w]:
        client.send(b"UP")
    elif keys[K_s]:
        client.send(b"DOWN")