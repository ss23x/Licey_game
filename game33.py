import pygame
import random
import time
import csv
import os


pygame.init()


# константы
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

# Цвета
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
PURPLE = (154, 102, 203)
SKY = (100, 149, 237)

# Создание игрового окна
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("Survival Racing")

# Загрузка шрифтов
FONT_SMALL = pygame.font.SysFont('arial', 24)
FONT_MEDIUM = pygame.font.SysFont('arial', 36)
FONT_LARGE = pygame.font.SysFont('arial', 48)

# Файл для сохранения результатов
SCORE_FILE = "scores.csv"

# Глобальные переменные для настроек
volume = 0.5  # Громкость звука (от 0 до 1)
music_enabled = True  # Включена ли музыка
fullscreen = False  # Флаг полноэкранного режима
controls_inverted = False  # Инверсия управления
difficulty = 1  # Уровень сложности (1 - легкий, 2 - средний, 3 - сложный)


# Классы игры


class Car(pygame.sprite.Sprite):
    """
    Класс игрока — машина.
    Управляет позицией, скоростью и улучшениями (ускорение, щит).
    """
    def __init__(self):
        super().__init__()
        self.images = [pygame.transform.scale(pygame.image.load(f'player{i}.png'), (50, 60)) for i in range(1, 9)]
        self.image = self.images[0]
        self.rect = self.image.get_rect()
        self.rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT - 100)
        self.speed = 5
        self.shield = 0  # количество активных щитов
        self.t = 0

    def update(self, keys_pressed, dt):
        self.t += dt
        self.image = self.images[int(self.t // 1) % len(self.images)]
        """Обновление позиции машины по нажатым клавишам."""
        if controls_inverted:
            if keys_pressed[pygame.K_LEFT] and self.rect.right < SCREEN_WIDTH:
                self.rect.x += self.speed
            if keys_pressed[pygame.K_RIGHT] and self.rect.left > 0:
                self.rect.x -= self.speed
        else:
            if keys_pressed[pygame.K_LEFT] and self.rect.left > 0:
                self.rect.x -= self.speed
            if keys_pressed[pygame.K_RIGHT] and self.rect.right < SCREEN_WIDTH:
                self.rect.x += self.speed
        if keys_pressed[pygame.K_UP] and self.rect.top > 0:
            self.rect.y -= self.speed
        if keys_pressed[pygame.K_DOWN] and self.rect.bottom < SCREEN_HEIGHT:
            self.rect.y += self.speed

    def upgrade(self, upgrade_type):
        """Применение улучшения: увеличение скорости или добавление щита."""
        if upgrade_type == "speed":
            self.speed += 2
        elif upgrade_type == "shield":
            self.shield += 1
            # Меняем цвет машины, чтобы показать, что щит активен
            #self.image.fill(YELLOW)

class Obstacle(pygame.sprite.Sprite):
    """
    Класс препятствия — случайно генерируемый объект (другая машина или препятствие).
    Скорость препятствия зависит от уровня сложности.
    """
    def __init__(self, level=1):
        super().__init__()
        width = random.randint(40, 70)
        height = random.randint(40, 70)
        self.image = pygame.transform.scale(pygame.image.load('obstacle.png'), (width, height))
        #self.image = pygame.Surface((width, height))
        #self.image.fill(BLUE)
        self.rect = self.image.get_rect()
        self.rect.x = random.randint(0, SCREEN_WIDTH - width)
        self.rect.y = -height
        self.speed = 3 + level  # чем выше уровень, тем быстрее препятствие

    def update(self):
        """Движение препятствия вниз и сброс позиции, если оно вышло за экран."""
        self.rect.y += self.speed
        if self.rect.top > SCREEN_HEIGHT:
            self.reset()

    def reset(self):
        """Сброс позиции препятствия наверх экрана с новой случайной позицией."""
        self.rect.x = random.randint(0, SCREEN_WIDTH - self.rect.width)
        self.rect.y = -self.rect.height

class Upgrade(pygame.sprite.Sprite):
    """
    Класс улучшения для машины.
    Может быть двух типов: 'speed' — ускорение, 'shield' — защита.
    """
    def __init__(self, upgrade_type):
        super().__init__()
        self.upgrade_type = upgrade_type
        self.image = pygame.Surface((30, 30))
        if upgrade_type == "speed":
            self.image = pygame.transform.scale(pygame.image.load('energy.png'), (50, 60))
        elif upgrade_type == "shield":
            self.image = pygame.transform.scale(pygame.image.load('shield.png'), (50, 60))
        self.rect = self.image.get_rect()
        self.rect.x = random.randint(0, SCREEN_WIDTH - self.rect.width)
        self.rect.y = -self.rect.height
        self.speed = 4

    def update(self):
        """Движение улучшения вниз по экрану."""
        self.rect.y += self.speed
        if self.rect.top > SCREEN_HEIGHT:
            self.kill()  # удаляем спрайт, если он ушел за экран


# Система достижений


class Achievement:
    def __init__(self, name, description):
        self.name = name
        self.description = description
        self.completed = False

    def complete(self):
        self.completed = True

achievements = [
    Achievement("First Steps", "Score 100 points in a single game"),
    Achievement("Shield Master", "Collect 3 shields in a single game"),
    Achievement("Speed Demon", "Reach level 5"),
    Achievement("Survivor", "Survive for 5 minutes"),
    Achievement("High Scorer", "Beat the high score"),
]

def achievements_menu():
    menu_running = True
    while menu_running:
        screen.fill(WHITE)
        screen.blit(bg, (0, 0))
        title_text = FONT_LARGE.render("Achievements", True, BLACK)
        screen.blit(title_text, (SCREEN_WIDTH // 2 - title_text.get_width() // 2, 50))

        y_offset = 120  # Уменьшаем начальный отступ
        for achievement in achievements:
            color = GREEN if achievement.completed else BLACK
            # Рисуем черный кружок слева от названия достижения
            pygame.draw.circle(screen, BLACK, (40, y_offset + 15), 10)
            name_text = FONT_SMALL.render(achievement.name, True, color)  # Используем меньший шрифт
            desc_text = FONT_SMALL.render(achievement.description, True, color)
            screen.blit(name_text, (60, y_offset))  # Уменьшаем отступ слева
            screen.blit(desc_text, (60, y_offset + 30))  # Уменьшаем вертикальный отступ
            y_offset += 60  # Уменьшаем отступ между достижениями

        back_text = FONT_MEDIUM.render("Press ESC to return", True, BLACK)
        screen.blit(back_text, (SCREEN_WIDTH // 2 - back_text.get_width() // 2, SCREEN_HEIGHT - 80))  # Поднимаем текст выше

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                menu_running = False
                pygame.quit()
                return
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return

        pygame.display.flip()
        pygame.time.delay(100)


# Функции для работы с результатами


def save_score(score):
    """
    Сохраняет результат игры в CSV-файл.
    Если файл не существует, создается с заголовком.
    """
    file_exists = os.path.isfile(SCORE_FILE)
    with open(SCORE_FILE, mode='a', newline='') as csv_file:
        writer = csv.writer(csv_file)
        if not file_exists:
            writer.writerow(["Score", "Timestamp"])
        writer.writerow([score, time.strftime("%Y-%m-%d %H:%M:%S")])

def load_high_score():
    """
    Загружает лучший результат из CSV-файла.
    Если файла нет, возвращается 0.
    """
    if not os.path.isfile(SCORE_FILE):
        return 0
    high_score = 0
    with open(SCORE_FILE, mode='r') as csv_file:
        reader = csv.reader(csv_file)
        next(reader, None)  # пропускаем заголовок
        for row in reader:
            try:
                score = int(row[0])
                if score > high_score:
                    high_score = score
            except:
                continue
    return high_score

# Экран выбора уровня сложности


def difficulty_menu():
    """Отображение меню выбора уровня сложности."""
    menu_running = True
    while menu_running:
        screen.fill(WHITE)
        screen.blit(bg, (0, 0))
        title_text = FONT_LARGE.render("Выберите уровень сложности", True, BLACK)
        easy_text = FONT_MEDIUM.render("1 - Легкий", True, BLACK)
        medium_text = FONT_MEDIUM.render("2 - Средний", True, PURPLE)
        hard_text = FONT_MEDIUM.render("3 - Сложный", True, RED)
        back_text = FONT_MEDIUM.render("Press ESC to return to Main Menu", True, BLACK)

        screen.blit(title_text, (SCREEN_WIDTH // 2 - title_text.get_width() // 2, SCREEN_HEIGHT // 4))
        screen.blit(easy_text, (SCREEN_WIDTH // 2 - easy_text.get_width() // 2, SCREEN_HEIGHT // 2))
        screen.blit(medium_text, (SCREEN_WIDTH // 2 - medium_text.get_width() // 2, SCREEN_HEIGHT // 2 + 50))
        screen.blit(hard_text, (SCREEN_WIDTH // 2 - hard_text.get_width() // 2, SCREEN_HEIGHT // 2 + 100))
        screen.blit(back_text, (SCREEN_WIDTH // 2 - back_text.get_width() // 2, SCREEN_HEIGHT // 2 + 150))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                menu_running = False
                pygame.quit()
                return
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    game_loop(1)  # Легкий уровень
                elif event.key == pygame.K_2:
                    game_loop(2)  # Средний уровень
                elif event.key == pygame.K_3:
                    game_loop(3)  # Сложный уровень
                elif event.key == pygame.K_ESCAPE:  # Возврат в главное меню
                    return

        pygame.display.flip()
        pygame.time.delay(100)


# Экран стартового меню


def start_menu():
    """Отображение стартового меню с инструкцией и ожиданием нажатия SPACE."""
    menu_running = True
    while menu_running:
        screen.fill(WHITE)
        screen.blit(bg, (0, 0))
        title_text = FONT_LARGE.render("Гонки на выживание", True, BLACK)
        instruction_text = FONT_MEDIUM.render("Нажмите ПРОБЕЛ, чтобы начать", True, BLACK)
        achievements_text = FONT_MEDIUM.render("Нажмите A, чтобы посмотреть достижения", True, BLACK)
        settings_text = FONT_MEDIUM.render("Нажмите S, чтобы открыть настройки", True, BLACK)
        quit_text = FONT_MEDIUM.render("Нажмите Q, чтобы выйти из игры", True, BLACK)
        info_text = FONT_SMALL.render("Используйте стрелки для управления. Собирайте улучшения и избегайте препятствий.", True, BLACK)

        screen.blit(title_text, (SCREEN_WIDTH // 2 - title_text.get_width() // 2, SCREEN_HEIGHT // 4))
        screen.blit(instruction_text, (SCREEN_WIDTH // 2 - instruction_text.get_width() // 2, SCREEN_HEIGHT // 2))
        screen.blit(achievements_text, (SCREEN_WIDTH // 2 - achievements_text.get_width() // 2, SCREEN_HEIGHT // 2 + 50))
        screen.blit(settings_text, (SCREEN_WIDTH // 2 - settings_text.get_width() // 2, SCREEN_HEIGHT // 2 + 100))
        screen.blit(quit_text, (SCREEN_WIDTH // 2 - quit_text.get_width() // 2, SCREEN_HEIGHT // 2 + 150))
        screen.blit(info_text, (SCREEN_WIDTH // 2 - info_text.get_width() // 2, SCREEN_HEIGHT // 2 + 200))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                menu_running = False
                pygame.quit()
                return
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    difficulty_menu()  # Переход к выбору уровня сложности
                if event.key == pygame.K_a:  # Открываем окно достижений
                    achievements_menu()
                if event.key == pygame.K_s:  # Открываем окно настроек
                    settings_menu()
                if event.key == pygame.K_q:  # Выход из игры
                    pygame.quit()
                    return
                if event.key == pygame.K_F11:  # Переключение полноэкранного режима
                    toggle_fullscreen()

        pygame.display.flip()
        pygame.time.delay(100)


# Экран завершения игры (Game Over)


def game_over_screen(score):
    """
    Отображает экран Game Over, сохраняет результат, показывает текущий счет и рекорд.
    Позволяет начать игру заново или выйти.
    """

    high_score = load_high_score()
    is_new_high_score = score > high_score
    save_score(score)
    over_running = True
    while over_running:
        screen.fill(WHITE)
        screen.blit(bg, (0, 0))
        game_over_text = FONT_LARGE.render("Game Over", True, RED)
        score_text = FONT_MEDIUM.render(f"Score: {score}", True, BLACK)
        high_score_text = FONT_MEDIUM.render(f"High Score: {high_score}", True, BLACK)
        restart_text = FONT_SMALL.render("Press R to Restart or Q to Quit", True, BLACK)
        menu_text = FONT_SMALL.render("Press M to return to Main Menu", True, BLACK)
        achievements_text = FONT_SMALL.render("Press A to view Achievements", True, BLACK)

        screen.blit(game_over_text, (SCREEN_WIDTH // 2 - game_over_text.get_width() // 2, SCREEN_HEIGHT // 4))
        screen.blit(score_text, (SCREEN_WIDTH // 2 - score_text.get_width() // 2, SCREEN_HEIGHT // 4 + 60))
        screen.blit(high_score_text, (SCREEN_WIDTH // 2 - high_score_text.get_width() // 2, SCREEN_HEIGHT // 4 + 120))

        # Поздравление с новым рекордом
        if is_new_high_score:
            congrats_text = FONT_MEDIUM.render("New High Score! Congratulations!", True, GREEN)
            screen.blit(congrats_text, (SCREEN_WIDTH // 2 - congrats_text.get_width() // 2, SCREEN_HEIGHT // 4 + 180))

        # Инструкция о перезапуске или выходе
        screen.blit(restart_text, (SCREEN_WIDTH // 2 - restart_text.get_width() // 2, SCREEN_HEIGHT // 4 + 240))
        screen.blit(menu_text, (SCREEN_WIDTH // 2 - menu_text.get_width() // 2, SCREEN_HEIGHT // 4 + 270))
        screen.blit(achievements_text, (SCREEN_WIDTH // 2 - achievements_text.get_width() // 2, SCREEN_HEIGHT // 4 + 300))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                over_running = False
                pygame.quit()
                return
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    difficulty_menu()  # Возврат к выбору уровня сложности
                elif event.key == pygame.K_q:
                    over_running = False
                    pygame.quit()
                    return
                elif event.key == pygame.K_m:  # Возврат в главное меню
                    over_running = False
                    start_menu()
                    return
                elif event.key == pygame.K_a:  # Открыть достижения
                    achievements_menu()
                if event.key == pygame.K_F11:  # Переключение полноэкранного режима
                    toggle_fullscreen()

        pygame.display.flip()
        pygame.time.delay(100)


# Меню паузы


def pause_menu():
    """Отображение меню паузы."""
    paused = True
    while paused:
        screen.fill(WHITE)
        screen.blit(bg, (0, 0))
        pause_text = FONT_LARGE.render("Paused", True, BLACK)
        resume_text = FONT_MEDIUM.render("Press P to Resume", True, BLACK)
        quit_text = FONT_MEDIUM.render("Press Q to Quit to Main Menu", True, BLACK)
        achievements_text = FONT_MEDIUM.render("Press A to view Achievements", True, BLACK)

        screen.blit(pause_text, (SCREEN_WIDTH // 2 - pause_text.get_width() // 2, SCREEN_HEIGHT // 4))
        screen.blit(resume_text, (SCREEN_WIDTH // 2 - resume_text.get_width() // 2, SCREEN_HEIGHT // 2))
        screen.blit(quit_text, (SCREEN_WIDTH // 2 - quit_text.get_width() // 2, SCREEN_HEIGHT // 2 + 50))
        screen.blit(achievements_text, (SCREEN_WIDTH // 2 - achievements_text.get_width() // 2, SCREEN_HEIGHT // 2 + 100))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_p:  # Продолжить игру
                    paused = False
                elif event.key == pygame.K_q:  # Выйти в главное меню
                    return "quit"
                elif event.key == pygame.K_a:  # Открыть достижения
                    achievements_menu()
                if event.key == pygame.K_F11:  # Переключение полноэкранного режима
                    toggle_fullscreen()

        pygame.display.flip()
        pygame.time.delay(100)


# Подтверждение выхода или перезапуска


def confirm_exit_or_restart():
    """Отображение меню подтверждения выхода или перезапуска."""
    confirm_running = True
    while confirm_running:
        screen.fill(WHITE)
        screen.blit(bg, (0, 0))
        confirm_text = FONT_LARGE.render("Are you sure?", True, BLACK)
        restart_text = FONT_MEDIUM.render("Press R to Restart", True, BLACK)
        quit_text = FONT_MEDIUM.render("Press Q to Quit", True, BLACK)
        menu_text = FONT_MEDIUM.render("Press M to return to Main Menu", True, BLACK)
        back_text = FONT_MEDIUM.render("Press ESC to return to game", True, BLACK)

        screen.blit(confirm_text, (SCREEN_WIDTH // 2 - confirm_text.get_width() // 2, SCREEN_HEIGHT // 4))
        screen.blit(restart_text, (SCREEN_WIDTH // 2 - restart_text.get_width() // 2, SCREEN_HEIGHT // 2))
        screen.blit(quit_text, (SCREEN_WIDTH // 2 - quit_text.get_width() // 2, SCREEN_HEIGHT // 2 + 50))
        screen.blit(menu_text, (SCREEN_WIDTH // 2 - menu_text.get_width() // 2, SCREEN_HEIGHT // 2 + 100))
        screen.blit(back_text, (SCREEN_WIDTH // 2 - back_text.get_width() // 2, SCREEN_HEIGHT // 2 + 150))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:  # Перезапуск игры
                    return "restart"
                elif event.key == pygame.K_q:  # Выход
                    return "quit"
                elif event.key == pygame.K_m:  # Возврат в главное меню
                    return "menu"
                elif event.key == pygame.K_ESCAPE:  # Возврат в игру
                    return "back"
                if event.key == pygame.K_F11:  # Переключение полноэкранного режима
                    toggle_fullscreen()

        pygame.display.flip()
        pygame.time.delay(100)

# Переключение полноэкранного режима


def toggle_fullscreen():
    """Переключение между полноэкранным и оконным режимом."""
    global fullscreen, SCREEN_WIDTH, SCREEN_HEIGHT
    fullscreen = not fullscreen
    if fullscreen:
        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
    else:
        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)


# Меню настроек

def settings_menu():
    global volume, music_enabled, fullscreen, controls_inverted, difficulty
    settings_running = True
    while settings_running:
        screen.fill(WHITE)
        screen.blit(bg, (0, 0))
        settings_text = FONT_LARGE.render("Settings", True, BLACK)
        volume_text = FONT_MEDIUM.render(f"Volume: {int(volume * 100)}% (UP/DOWN to adjust)", True, BLACK)
        music_text = FONT_MEDIUM.render(f"Music: {'On' if music_enabled else 'Off'} (Press F to toggle)", True, BLACK)
        fullscreen_text = FONT_MEDIUM.render(f"Fullscreen: {'On' if fullscreen else 'Off'} (Press F11 to toggle)", True, BLACK)
        controls_text = FONT_MEDIUM.render(f"Controls: {'Inverted' if controls_inverted else 'Normal'} (Press I to toggle)", True, BLACK)
        difficulty_text = FONT_MEDIUM.render(f"Difficulty: {['Easy', 'Medium', 'Hard'][difficulty - 1]} (Press 1-3 to change)", True, BLACK)
        back_text = FONT_MEDIUM.render("Press ESC to return", True, BLACK)
        menu_text = FONT_MEDIUM.render("Press M to return to Main Menu", True, BLACK)
        keys_text1 = FONT_SMALL.render("In-game keys: P - Pause, ESC - Settings, R - Restart, Q - Quit", True, BLACK)
        keys_text2 = FONT_SMALL.render("M - Main Menu, A - Achievements, F11 - Fullscreen", True, BLACK)

        screen.blit(settings_text, (SCREEN_WIDTH // 2 - settings_text.get_width() // 2, 50))
        screen.blit(volume_text, (50, 120))
        screen.blit(music_text, (50, 160))
        screen.blit(fullscreen_text, (50, 200))
        screen.blit(controls_text, (50, 240))
        screen.blit(difficulty_text, (50, 280))
        screen.blit(back_text, (SCREEN_WIDTH // 2 - back_text.get_width() // 2, SCREEN_HEIGHT - 120))
        screen.blit(menu_text, (SCREEN_WIDTH // 2 - menu_text.get_width() // 2, SCREEN_HEIGHT - 160))
        screen.blit(keys_text1, (50, SCREEN_HEIGHT - 240))
        screen.blit(keys_text2, (50, SCREEN_HEIGHT - 210))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:  # Возврат в игру
                    return
                if event.key == pygame.K_UP:  # Увеличение громкости
                    volume = min(1.0, volume + 0.1)
                if event.key == pygame.K_DOWN:  # Уменьшение громкости
                    volume = max(0.0, volume - 0.1)
                if event.key == pygame.K_f:  # Включение/выключение музыки
                    music_enabled = not music_enabled
                if event.key == pygame.K_F11:  # Переключение полноэкранного режима
                    toggle_fullscreen()
                if event.key == pygame.K_i:  # Инверсия управления
                    controls_inverted = not controls_inverted
                if event.key == pygame.K_1:  # Установка уровня сложности
                    difficulty = 1
                if event.key == pygame.K_2:
                    difficulty = 2
                if event.key == pygame.K_3:
                    difficulty = 3
                if event.key == pygame.K_m:  # Возврат в главное меню
                    result = confirm_exit_or_restart()
                    if result == "menu":
                        start_menu()
                        return

        pygame.display.flip()
        pygame.time.delay(100)


# Основной игровой цикл


bg = pygame.image.load('bg.jpg')

def game_loop(difficulty_level):
    clock = pygame.time.Clock()
    running = True
    score = 0
    level = difficulty_level  # Начальный уровень зависит от выбранной сложности

    # Группы спрайтов
    all_sprites = pygame.sprite.Group()
    obstacles = pygame.sprite.Group()
    upgrades = pygame.sprite.Group()

    # Создаем игрока (машину)
    player = Car()
    all_sprites.add(player)

    # Добавляем несколько начальных препятствий
    for i in range(3):
        obs = Obstacle(level)
        obstacles.add(obs)
        all_sprites.add(obs)

    # Таймер для появления улучшений
    upgrade_timer = 0

    # Загружаем текущий рекорд
    high_score = load_high_score()

    while running:
        dt = clock.tick(FPS) / 1000

        # Обработка событий
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                pygame.quit()
                return
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_p:  # Пауза при нажатии P
                    result = pause_menu()
                    if result == "quit":  # Если игрок выбрал выход в главное меню
                        return
                if event.key == pygame.K_ESCAPE:  # Открыть меню настроек при нажатии ESC
                    settings_menu()
                if event.key == pygame.K_r or event.key == pygame.K_q or event.key == pygame.K_m:  # Перезапуск, выход или возврат в меню
                    result = confirm_exit_or_restart()
                    if result == "restart":
                        game_loop(difficulty_level)  # Перезапуск игры
                        return
                    elif result == "quit":
                        game_over_screen(score)  # Завершение игры с сохранением счета
                        return
                    elif result == "menu":
                        start_menu()  # Возврат в главное меню
                        return
                    elif result == "back":
                        continue  # Возврат в игру
                if event.key == pygame.K_a:  # Открыть достижения
                    achievements_menu()
                if event.key == pygame.K_F11:  # Переключение полноэкранного режима
                    toggle_fullscreen()

        keys_pressed = pygame.key.get_pressed()  # Получаем состояние клавиш
        player.update(keys_pressed, dt)  # Обновляем игрока (машину)

        # Обновление всех спрайтов (поочередно)
        for sprite in all_sprites:
            if isinstance(sprite, Car):
                sprite.update(keys_pressed, dt)  # Для машины передаем keys_pressed
            else:
                sprite.update()  # Для остальных спрайтов вызываем update без аргументов

        # Увеличение счета и переход на новый уровень
        score += 1
        if score % 200 == 0:
            level += 1
            # Добавляем новое препятствие с учетом возросшего уровня
            new_obs = Obstacle(level)
            obstacles.add(new_obs)
            all_sprites.add(new_obs)

        # Появление улучшений каждые 500 тактов
        upgrade_timer += 1
        if upgrade_timer > 500:
            upgrade_timer = 0
            upgrade_type = random.choice(["speed", "shield"])
            new_upgrade = Upgrade(upgrade_type)
            upgrades.add(new_upgrade)
            all_sprites.add(new_upgrade)

        # Проверка коллизий с препятствиями
        collided_obstacle = pygame.sprite.spritecollideany(player, obstacles)
        if collided_obstacle:
            if player.shield > 0:
                # Если щит активен, сбрасываем препятствие и уменьшаем щит
                collided_obstacle.reset()
                player.shield -= 1
                # Сброс цвета машины при исчерпании щита
                #if player.shield == 0:
                    #player.image.fill(RED)
            else:
                running = False
                game_over_screen(score)
                return

        # Проверка коллизий с улучшениями
        collided_upgrade = pygame.sprite.spritecollideany(player, upgrades)
        if collided_upgrade:
            player.upgrade(collided_upgrade.upgrade_type)
            collided_upgrade.kill()

        # Проверка достижений
        if score >= 100 and not achievements[0].completed:
            achievements[0].complete()
        if player.shield >= 3 and not achievements[1].completed:
            achievements[1].complete()
        if level >= 5 and not achievements[2].completed:
            achievements[2].complete()
        if pygame.time.get_ticks() >= 300000 and not achievements[3].completed:
            achievements[3].complete()
        if score > high_score and not achievements[4].completed:
            achievements[4].complete()

        # Отрисовка фона и всех спрайтов
        screen.fill(WHITE)
        screen.blit(bg, (0, 0))
        all_sprites.draw(screen)

        # Отображение счета, уровня, количества щитов и рекорда
        score_text = FONT_SMALL.render(f"Score: {score}", True, BLACK)
        level_text = FONT_SMALL.render(f"Level: {level}", True, BLACK)
        shield_text = FONT_SMALL.render(f"Shield: {player.shield}", True, BLACK)
        high_score_text = FONT_SMALL.render(f"High Score: {high_score}", True, BLACK)
        screen.blit(score_text, (10, 10))
        screen.blit(level_text, (10, 40))
        screen.blit(shield_text, (10, 70))
        screen.blit(high_score_text, (10, 100))

        # Отображение оставшихся очков до нового рекорда
        if score < high_score:
            remaining_score_text = FONT_SMALL.render(f"Remaining to beat high score: {high_score - score}", True, BLACK)
            screen.blit(remaining_score_text, (10, 130))

        pygame.display.flip()

    pygame.quit()

# Основная точка входа в игру

def main():
    """Основная точка входа в игру."""
    start_menu()

if __name__ == "__main__":
    main()

#done