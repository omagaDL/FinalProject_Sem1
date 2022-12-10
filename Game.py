import time as time_lib
import pygame
import sys
from pygame.locals import *
from level import *
from enimies import *
import random
import player


pygame.init()
FILE_DIR = os.path.dirname(__file__)
size = width, height = 800, 600  # размерчик нужно будет поменять
level_h, level_w = 0, 0
clock = pygame.time.Clock()  # вот тут вот вообще лучше ничего не трогать(и на строку ниже тоже)
screen = pygame.display.set_mode(size)
pygame.display.set_caption("The_deadly_wave")
FPS = 50
BACK = ['fon.png', "hero_choose.jpg", 'game_fon_1', 'game_fon']  # здесь будут фоны
sound = 0
phase = 'start_screen'
all_sprites = pygame.sprite.Group()
death = pygame.mixer.Sound('data_death.wav')
hero = None
time_ = 0
time_record = 0
time_start = 0
new_game = 1
was_paused = False
character = 'samus'
control = 'Arrows'
platforms = []
mousepos = [0,0]
chx = 0
chy = 0


COLORS = [RED, BRIGHTRED, GREEN, BRIGHTGREEN] = [(220, 0, 0), (255, 0, 0), (100, 200, 100), (100, 255, 100)]


class Camera(object):
    def __init__(self, camera_func, width, height):
        self.camera_func = camera_func
        self.state = Rect(0, 0, width, height)

    def apply(self, target):
        return target.rect.move(self.state.topleft)

    def update(self, target):
        self.state = self.camera_func(self.state, target.rect)


def camera_configure(camera, target_rect):
    l, t, _, _ = target_rect
    _, _, w, h = camera
    l, t = -l + width / 2, -t + height / 2

    l = min(0, l)  # Не движемся дальше левой границы
    l = max(-(camera.width - width), l)  # Не движемся дальше правой границы
    t = max(-(camera.height - height), t)  # Не движемся дальше нижней границы
    t = min(0, t)  # Не движемся дальше верхней границы

    return Rect(l, t, w, h)


def loadLevel():
    global playerX, playerY, level_h, level_w, platforms, level  # объявляем глобальные переменные, это координаты героя

    level = []
    platforms = []
    levelFile = open('%s/levels/1.txt' % FILE_DIR)
    line = " "
    while line[0] != "/":  # пока не нашли символ завершения файла
        line = levelFile.readline()  # считываем построчно
        if line[0] == "[":  # если нашли символ начала уровня
            while line[0] != "]":  # то, пока не нашли символ конца уровня
                line = levelFile.readline()  # считываем построчно уровень
                if line[0] != "]":  # и если нет символа конца уровня
                    endLine = line.find("|")  # то ищем символ конца строки
                    level.append(
                        line[0: endLine])  # и добавляем в уровень строку от начала до символа "|"
                    # level_h += 1
                    # level_w = max(len(line) - 2, level_w)

        if line[0] != "":  # если строка не пустая
            commands = line.split()  # разбиваем ее на отдельные команды
            if len(commands) > 1:  # если количество команд > 1, то ищем эти команды
                if commands[0] == "player":  # если первая команда - player
                    playerX = int(commands[1])  # то записываем координаты героя
                    playerY = int(commands[2])
                if commands[0] == "portal":  # если первая команда portal, то создаем портал
                    tp = BlockTeleport(int(commands[1]), int(commands[2]), int(commands[3]),
                                       int(commands[4]))
                    all_sprites.add(tp)
                    platforms.append(tp)
                    animated.add(tp)
    x = y = 0  # координаты
    for row in level:  # вся строка
        for col in row:  # каждый символ
            if col == "-":
                pf = Platform(x, y)
                all_sprites.add(pf)
                platforms.append(pf)
            if col == "*":
                bd = BlockDie(x, y)
                all_sprites.add(bd)
                platforms.append(bd)

            x += PLATFORM_WIDTH  # блоки платформы ставятся на ширине блоков
        y += PLATFORM_HEIGHT  # то же самое и с высотой
        x = 0  # на каждой новой строчке начинаем с нуля


def text_render(inf, x, y, color1=GREEN, color2=GREEN, mousepos=[0, 0]):  # Рисует текст в рамке, меняющий цвет при
    # наведении мыши
    font = pygame.font.Font(None, 50)
    text = font.render(inf, 1, color1)
    text_w = text.get_width() + 20
    text_h = text.get_height() + 20
    if not (x - text_w / 2 <= mousepos[0] <= x + text_w / 2) or not (y - text_h / 2 <= mousepos[1] <= y + text_h / 2):
        screen.blit(text, (x - text.get_width() // 2, y - text.get_height() // 2))
        pygame.draw.rect(screen, color1,
                        (x - text_w // 2, y - text_h // 2,
                         text_w, text_h), 1)
    else:
        text = font.render(inf, 1, color2)
        screen.blit(text, (x - text.get_width() // 2, y - text.get_height() // 2))
        pygame.draw.rect(screen, color2,
                         (x - text_w // 2, y - text_h // 2,
                          text_w, text_h), 1)


def button(inf, x, y, event):  # Регистрирует нажатия на кнопку
    font = pygame.font.Font(None, 50)
    text = font.render(inf, 1, GREEN)
    text_w = text.get_width() + 20
    text_h = text.get_height() + 20
    if (x - text_w / 2 <= event.pos[0] <= x + text_w / 2) and (y - text_h / 2 <= event.pos[1] <= y + text_h / 2):
        return 1
    else:
        return 0


# для загрузки изображений
def load_image(name, colorkey=None):
    fullname = os.path.join(name)
    image = pygame.image.load(fullname)
    if colorkey is not None:
        if colorkey == -1:
            colorkey = image.get_at((0, 0))
        image.set_colorkey(colorkey)
    else:
        image = image.convert_alpha()
    return image


# для загрузки этих картинок)
def print_sprite(x, y, im):
    sprite_im = pygame.sprite.Sprite()
    sprite_im.image = load_image(im)
    sprite_im.rect = sprite_im.image.get_rect()
    all_sprites.add(sprite_im)
    sprite_im.rect.x = x
    sprite_im.rect.y = y
    return sprite_im


# сюда тоже лучше не лезть, она все вырубает
def terminate():
    pygame.quit()
    sys.exit()


def start_screen():
    global sound, phase, new_game, mousepos
    # x = width // 2 + 50
    # y = height // 2 - 50
    if new_game == 1:  # Чтобы музыка не начинала воспроизводиться заново при выходе из hero_choice
        pygame.mixer.music.load('data_title.mp3')
        pygame.mixer.music.play(-1)
    while True:
        fon = pygame.transform.scale(load_image(BACK[0]), (width, height))
        screen.blit(fon, (0, 0))
        pygame.display.flip()
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.MOUSEMOTION:
                mousepos = event.pos
            elif event.type == pygame.QUIT:
                terminate()
                return
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if width-50 < event.pos[0] < width-10 and 5 < event.pos[1] < 50:
                    if sound == 0:
                        sound = 1
                    else:
                        sound = 0
                elif button('Новая игра', width // 2, height // 2 - 50, event):
                    phase = 'gameplay'
                    return
                elif button('Выход', width // 2, height - 50, event):
                    terminate()
                elif button('Выбор героя', width // 2, height // 2 + 50, event):
                    phase = 'hero_choice'
                    return
                elif button('Выбор управления', width // 2, height // 2 + 150, event):
                    phase = 'control_choice'
                    return
        if sound == 0 and pygame.mixer.music.get_busy():
            pygame.mixer.music.stop()
        if sound == 1 and not pygame.mixer.music.get_busy():
            pygame.mixer.music.play(-1)
        text_render('Новая игра', width // 2, height // 2 - 50, GREEN, BRIGHTGREEN, mousepos)
        text_render('Выход', width // 2, height - 50,RED, BRIGHTRED,  mousepos)
        text_render('Выбор героя', width // 2, height // 2 + 50,GREEN, BRIGHTGREEN,  mousepos)
        text_render('Выбор управления', width // 2, height // 2 + 150,GREEN, BRIGHTGREEN, mousepos)
        if sound == 1:
            if (width - 50 < mousepos[0] < width - 10) and (
                    10 < mousepos[1] < 50):
                screen.blit(load_image('volume_2.png'), (width-50, 10))
            else:
                screen.blit(load_image('volume.png'), (width - 50, 10))
        else:
            if(width-50 < mousepos[0] < width - 10) and (
                    10 < mousepos[1] < 50):
                screen.blit(load_image('voice_off_2.png'), (width - 50, 10))
            else:
                screen.blit(load_image('voice_off.png'), (width-50, 10))
        pygame.display.update()


def score():
    global phase, time_record, new_game, mousepos
    new_game = 1
    if int(time_) > time_record:
        time_record = int(time_)
        record = True
    else:
        record = False
    pygame.mixer.music.stop()
    if sound == 1:
        death.play()
    fon = pygame.transform.scale(load_image(BACK[0]), (width, height))
    screen.blit(fon, (0, 0))
    text_render("Вы проиграли", width // 2, height // 2, BRIGHTRED)
    if record:
        text_render(f"Новый рекорд: {time_record}", width // 2, height // 4, BRIGHTGREEN)
    else:
        text_render(f"Ваше время: {int(time_)}, рекорд: {time_record}", width // 2, height // 4, BRIGHTRED)
    pygame.display.flip()
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                phase = 'start_screen'
                return
            elif event.type == pygame.MOUSEMOTION:
                mousepos = event.pos


def gameplay():
    global phase, hero, time_, all_sprites, level, mousepos, was_paused, time_start
    loadLevel()
    monsta = list()
    if not hero:
        hero = player.Player(playerX, playerY, character)  # создаем героя по (x, y) координатам
    else:
        hero.__init__(playerX, playerY, character)
    pygame.mixer.music.stop()
    if sound == 1:
        pygame.mixer.music.load('data_boss_fight.mp3')
        pygame.mixer.music.play(-1)
    fon = pygame.transform.scale(load_image(BACK[1]), (width, height))
    screen.blit(fon, (0, 0))
    animated.clear(fon, BACK[1])
    monsters.clear(fon, BACK[1])
    all_sprites.clear(fon, BACK[1])
    pygame.display.update()
    left = right = False  # по умолчанию - стоим
    up = False
    running = False
    game_start = False
    all_sprites.add(hero)

    timer = pygame.time.Clock()

    total_level_width = len(level[0]) * PLATFORM_WIDTH  # Высчитываем фактическую ширину уровня
    total_level_height = len(level) * PLATFORM_HEIGHT  # высоту

    camera = Camera(camera_configure, total_level_width, total_level_height)
    tm = 0
    tm_last = 0
    while not hero.dead:  # Основной цикл программы
        timer.tick(60)
        if game_start:    # Игра начинается только после начала движения
            tm += 1
        for e in pygame.event.get():  # Обрабатываем события
            if e.type == QUIT:
                terminate()
            if control == 'Arrows':  # Управление стрелочками
                if e.type == KEYDOWN and e.key == K_UP:
                    up = True
                    if not game_start:
                        time_start = time_lib.time()
                        game_start = True
                if e.type == KEYDOWN and e.key == K_LEFT:
                    left = True
                    if not game_start:
                        time_start = time_lib.time()
                        game_start = True
                if e.type == KEYDOWN and e.key == K_RIGHT:
                    right = True
                    if not game_start:
                        time_start = time_lib.time()
                        game_start = True
                if e.type == KEYDOWN and e.key == K_LSHIFT:
                    running = True

                if e.type == KEYUP and e.key == K_UP:
                    up = False
                if e.type == KEYUP and e.key == K_RIGHT:
                    right = False
                if e.type == KEYUP and e.key == K_LEFT:
                    left = False
                if e.type == KEYUP and e.key == K_LSHIFT:
                    running = False
            elif control == 'WASD':  # Управление WASD
                if e.type == KEYDOWN and e.key == K_w:
                    up = True
                    if not game_start:
                        time_start = time_lib.time()
                        game_start = True
                if e.type == KEYDOWN and e.key == K_a:
                    left = True
                    if not game_start:
                        time_start = time_lib.time()
                        game_start = True
                if e.type == KEYDOWN and e.key == K_d:
                    right = True
                    if not game_start:
                        time_start = time_lib.time()
                        game_start = True
                if e.type == KEYDOWN and e.key == K_LSHIFT:
                    running = True

                if e.type == KEYUP and e.key == K_w:
                    up = False
                if e.type == KEYUP and e.key == K_d:
                    right = False
                if e.type == KEYUP and e.key == K_a:
                    left = False
                if e.type == KEYUP and e.key == K_LSHIFT:
                    running = False
            if e.type == KEYDOWN and e.key == K_ESCAPE:
                was_paused = True
                phase = 'pause_menu'
                return
            if e.type == MOUSEMOTION:
                mousepos = e.pos
            if tm - tm_last > 50:
                tm_last = tm
                mn = Monster(random.randint(0, total_level_width), random.randint(0, total_level_height),
                             random.randint(0, 4), random.randint(0, 4), random.randint(0, 150), random.randint(0, 150))
                monsta.append(mn)
                all_sprites.add(mn)
                platforms.append(mn)
                monsters.add(mn)
        screen.blit(fon, (0, 0))
        animated.update()  # показываем анимацию
        monsters.update(platforms)  # передвигаем всех монстров
        camera.update(hero)  # центрируем камеру относительно персонажа
        hero.update(left, right, up, running, platforms)  # передвижение
        for e in all_sprites:
            screen.blit(e.image, camera.apply(e))
        pygame.display.update()  # обновление и вывод всех изменений на экран
    phase = 'score'
    for i in monsta:
        i.kill()
    del monsta
    for e in all_sprites:
        screen.blit(e.image, camera.apply(e))
    pygame.display.update()
    time_ = time_lib.time() - time_start

def hero_choice():
    characters = [['samus', width // 2 - 100, height // 2], ['mario', width // 2 + 100, height // 2]]
    global sound, phase, new_game, character, mousepos, was_paused
    new_game = 0
    fon = pygame.transform.scale(load_image(BACK[1]), (width, height))
    screen.blit(fon, (0, 0))
    while True:
        pygame.display.flip()
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.MOUSEMOTION:
                mousepos = event.pos
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if button('Назад', width // 2, height - 50, event) and not was_paused:
                    was_paused = False
                    phase = 'start_screen'
                    return
                elif button('Назад', width // 2, height - 50, event):
                    was_paused = True
                    phase = 'pause_menu'
                    return
                for i in characters:
                    if button(i[0], i[1], i[2], event):
                        character = i[0]
                        phase = 'start_screen'
                        return
        if sound == 0 and pygame.mixer.music.get_busy():
            pygame.mixer.music.stop()
        if sound == 1 and not pygame.mixer.music.get_busy():
            pygame.mixer.music.play(-1)
        text_render('Назад', width // 2, height - 50, RED, BRIGHTRED, mousepos)
        text_render('Samus', width // 2 - 100, height // 2, GREEN, BRIGHTGREEN, mousepos)
        text_render('Mario', width // 2 + 100, height // 2, GREEN, BRIGHTGREEN, mousepos)
        pygame.display.update()

def control_choice(): # Выбор управления
    controls = [['WASD', width // 2 - 100, height // 2], ['Arrows', width // 2 + 100, height // 2]]
    global sound, phase, new_game, control, mousepos, was_paused
    new_game = 0
    fon = pygame.transform.scale(load_image(BACK[1]), (width, height))
    screen.blit(fon, (0, 0))
    while True:
        pygame.display.flip()
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.MOUSEMOTION:
                mousepos = event.pos
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if button('Назад', width // 2, height - 50, event) and not was_paused:
                    phase = 'start_screen'
                    return
                elif button('Назад', width // 2, height - 50, event):
                    was_paused = True
                    phase = 'pause_menu'
                    return
                for i in controls:
                    if button(i[0], i[1], i[2], event):
                        control = i[0]
                        if not was_paused:
                            phase = 'start_screen'
                            return
                        else:
                            was_paused = True
                            phase = 'pause_menu'
                            return
        if sound == 0 and pygame.mixer.music.get_busy():
            pygame.mixer.music.stop()
        if sound == 1 and not pygame.mixer.music.get_busy():
            pygame.mixer.music.play(-1)
        text_render('Назад', width // 2, height - 50, RED, BRIGHTRED, mousepos)
        text_render('WASD', width // 2 - 100, height // 2, GREEN, BRIGHTGREEN, mousepos)
        text_render('Arrows', width // 2 + 100, height // 2, GREEN, BRIGHTGREEN, mousepos)
        pygame.display.update()

def pause_menu():
    global sound, phase, new_game, mousepos, was_paused
    fon = pygame.transform.scale(load_image(BACK[1]), (width, height))
    screen.blit(fon, (0, 0))
    while True:
        pygame.display.flip()
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.MOUSEMOTION:
                mousepos = event.pos
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if button('Продолжить игру', width // 2, height//2, event):
                    was_paused = True
                    phase = 'gameplay'
                    return
                elif button('Главное Меню', width//2, height - 50, event):
                    was_paused = False
                    phase = 'start_screen'
                    return
                elif button('Выбор управления', width // 2, height // 2 + 150, event):
                    was_paused = True
                    phase = 'control_choice'
                    return
        if sound == 0 and pygame.mixer.music.get_busy():
            pygame.mixer.music.stop()
        if sound == 1 and not pygame.mixer.music.get_busy():
            pygame.mixer.music.play(-1)
        text_render('Продолжить игру', width // 2, height // 2, RED, BRIGHTRED, mousepos)
        text_render('Выбор управления', width // 2, height // 2 + 150, GREEN, BRIGHTGREEN, mousepos)
        text_render('Главное Меню', width // 2, height - 50, GREEN, BRIGHTGREEN, mousepos)


animated = pygame.sprite.Group()  # все анимированные объекты, за исключением героя
monsters = pygame.sprite.Group()  # Все передвигающиеся объекты
while True:
    if phase == 'start_screen':
        start_screen()
    elif phase == 'score':
        all_sprites = pygame.sprite.Group()
        score()
    elif phase == 'gameplay':
        gameplay()
    elif phase == 'hero_choice':
        hero_choice()
    elif phase == 'control_choice':
        control_choice()
    elif phase == 'pause_menu':
        pause_menu()
