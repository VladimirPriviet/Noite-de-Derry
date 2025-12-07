import pygame
import sys
import math
import random
import os
import glob

# ===== CORREÇÃO DA IMPORTAÇÃO MOVIEPY =====
try:
    from moviepy.editor import VideoFileClip
    HAS_MOVIEPY = True
except ImportError:
    try:
        from moviepy import VideoFileClip
        HAS_MOVIEPY = True
    except ImportError:
        HAS_MOVIEPY = False
        print("AVISO: MoviePy não instalado. Os vídeos não serão exibidos.")

# ===== CONFIGURAÇÃO DE ÁUDIO =====
try: pygame.mixer.pre_init(44100, -16, 2, 2048)
except: pass
pygame.init()
try: pygame.mixer.init(44100, -16, 2, 2048)
except: pass

# ===== 1. CONFIGURAÇÕES =====
class Settings:
    SCREEN_WIDTH = 800
    SCREEN_HEIGHT = 600
    FPS = 60
    TILE_SIZE = 120  
    VOLUME = 0.3 

    # Cores
    COLOR_BG = (10, 10, 10)          
    COLOR_WALL = (80, 80, 80)     
    COLOR_WALL_3 = (130, 40, 40)     
    COLOR_FLOOR = (25, 30, 35)       

    # Cores do Poço
    COLOR_WELL_BG = (0, 0, 0)            
    COLOR_WELL_WALL = (25, 25, 25)       
    COLOR_WELL_FLOOR = (15, 10, 10)      
    COLOR_WELL_CRACKED = (20, 15, 15)    
    
    # Cores Batalha
    COLOR_UI_BG = (20, 20, 40)
    COLOR_UI_BORDER = (255, 255, 255)
    COLOR_TEXT = (255, 255, 255)
    COLOR_HIGHLIGHT = (255, 255, 0)

# ===== 2. SISTEMA DE BATALHA =====
class BattleSystem:
    def __init__(self, game):
        self.game = game
        self.font = pygame.font.SysFont("Courier New", 24, bold=True)
        
        self.player_hp = 100
        self.player_max_hp = 100
        self.enemy_hp = 500
        self.enemy_max_hp = 500
        
        self.state = "MENU" 
        self.message = "IT quer brincar..."
        self.action_cooldown = 0
        self.options = ["PEDRA", "XINGAR", "CURAR", "MATURIN"]
        self.selected_index = 0

        # Imagens
        try: self.bg_img = pygame.transform.scale(pygame.image.load("battle_bg.png").convert(), (Settings.SCREEN_WIDTH, Settings.SCREEN_HEIGHT))
        except: self.bg_img = None
        try: self.player_back = pygame.transform.scale(pygame.image.load("player_back.png").convert_alpha(), (250, 250))
        except: self.player_back = None
        try: self.enemy_img = pygame.transform.scale(pygame.image.load("image_17.png").convert_alpha(), (300, 400))
        except: self.enemy_img = None
        
        # Ataques
        try: self.stone_proj = pygame.transform.scale(pygame.image.load("pedram.png").convert_alpha(), (60, 60))
        except: self.stone_proj = pygame.Surface((40,40)); self.stone_proj.fill((150,150,150))
        try: self.maturin_img = pygame.transform.scale(pygame.image.load("maturin.png").convert_alpha(), (400, 400))
        except: self.maturin_img = pygame.Surface((400,400)); self.maturin_img.fill((0,255,255))

        # Som de ataque
        try: self.attack_sound = pygame.mixer.Sound("ps.mp3"); self.attack_sound.set_volume(Settings.VOLUME)
        except: self.attack_sound = None

        self.anim_timer = 0
        self.proj_x = 0; self.proj_y = 0

        # Imagens extras do IT
        img_size = (300, 400)
        try: self.enemy_img_idle = self.enemy_img
        except: self.enemy_img_idle = None
        try: self.enemy_img_l = pygame.transform.scale(pygame.image.load("itl.png").convert_alpha(), img_size)
        except: self.enemy_img_l = self.enemy_img
        try: self.enemy_img_a = pygame.transform.scale(pygame.image.load("ita.png").convert_alpha(), img_size)
        except: self.enemy_img_a = self.enemy_img
        try: self.enemy_img_c = pygame.transform.scale(pygame.image.load("itc.png").convert_alpha(), img_size)
        except: self.enemy_img_c = self.enemy_img

        self.current_enemy_img = self.enemy_img_idle

        self.enemy_attacks = [
            {"img": self.enemy_img_l, "min": 10, "max": 20, "msg": "IT sorri..."},
            {"img": self.enemy_img_a, "min": 20, "max": 35, "msg": "IT avanca!"},
            {"img": self.enemy_img_c, "min": 5, "max": 50, "msg": "IT se transforma!"},
        ]

    def start_battle(self, pennywise_sprite=None):
        self.message = "IT BLOQUEIA O CAMINHO!"
        self.state = "MENU"
        self.current_enemy_img = self.enemy_img_idle

    def draw_bar(self, screen, x, y, hp, max_hp, color):
        pygame.draw.rect(screen, (50, 50, 50), (x, y, 200, 20))
        ratio = max(0, hp) / max_hp
        pygame.draw.rect(screen, color, (x, y, 200 * ratio, 20))
        pygame.draw.rect(screen, (255, 255, 255), (x, y, 200, 20), 2)

    def update(self):
        keys = pygame.key.get_pressed()
        if self.action_cooldown > 0:
            self.action_cooldown -= 1
            return

        if self.state == "MENU":
            if keys[pygame.K_RIGHT]: self.selected_index = (self.selected_index + 1) % len(self.options); self.action_cooldown = 10
            if keys[pygame.K_LEFT]: self.selected_index = (self.selected_index - 1) % len(self.options); self.action_cooldown = 10
            if keys[pygame.K_z]: self.execute_move(); self.action_cooldown = 30

        elif self.state == "ANIM_STONE":
            target_x, target_y = Settings.SCREEN_WIDTH - 200, 150
            dx, dy = target_x - self.proj_x, target_y - self.proj_y
            dist = math.hypot(dx, dy)
            if dist < 20:
                dmg = random.randint(40, 80); self.enemy_hp -= dmg; self.message = f"A pedra acertou! -{dmg} HP"; self.check_win()
            else:
                self.proj_x += (dx/dist)*25; self.proj_y += (dy/dist)*25

        elif self.state == "ANIM_MATURIN":
            self.anim_timer -= 1
            if self.anim_timer <= 0:
                dmg = self.enemy_max_hp // 2; self.enemy_hp -= dmg; self.message = f"MATURIN ESMAGOU O IT! -{dmg} HP"; self.check_win()

        elif self.state == "ENEMY_TURN":
            if self.action_cooldown == 0:
                if self.attack_sound: self.attack_sound.play()
                atk = random.choice(self.enemy_attacks)
                dmg = random.randint(atk["min"], atk["max"])
                self.player_hp -= dmg
                self.message = f"{atk['msg']} -{dmg} HP"
                self.current_enemy_img = atk["img"]
                self.state = "ENEMY_ANIM"; self.anim_timer = 90
                if self.player_hp <= 0: self.state = "LOSE"; self.message = "VOCE FLUTUOU..."

        elif self.state == "ENEMY_ANIM":
            self.anim_timer -= 1
            if self.anim_timer <= 0:
                self.current_enemy_img = self.enemy_img_idle
                self.state = "MENU"; self.action_cooldown = 30
        
        elif self.state == "WIN":
            pass

    def check_win(self):
        if self.enemy_hp <= 0: 
            self.state = "WIN"
            self.message = "VITORIA! APERTE 'P' PARA ACABAR."
        else: 
            self.state = "ENEMY_TURN"
            self.action_cooldown = 60

    def execute_move(self):
        move = self.options[self.selected_index]
        if move == "PEDRA":
            self.state = "ANIM_STONE"; self.proj_x = 150; self.proj_y = 400; self.message = "Voce lancou uma pedra!"
        elif move == "MATURIN":
            self.state = "ANIM_MATURIN"; self.anim_timer = 180; self.message = "INVOCANDO MATURIN..."
        elif move == "XINGAR":
            dmg = random.randint(5, 15); self.enemy_hp -= dmg; self.message = "Voce xingou o IT!"; self.check_win()
        elif move == "CURAR":
            heal = 40; self.player_hp = min(self.player_max_hp, self.player_hp + heal); self.message = "Recuperou vida."; self.state = "ENEMY_TURN"; self.action_cooldown = 60

    def draw(self, screen):
        if self.bg_img: screen.blit(self.bg_img, (0,0))
        else: screen.fill((20, 5, 5))
        
        if self.current_enemy_img: 
            screen.blit(self.current_enemy_img, (Settings.SCREEN_WIDTH - 350, 50))
        
        if self.player_back: screen.blit(self.player_back, (50, Settings.SCREEN_HEIGHT - 300))
        else: pygame.draw.rect(screen, (0, 0, 200), (50, 350, 150, 150))
        
        if self.state == "ANIM_STONE": screen.blit(self.stone_proj, (int(self.proj_x), int(self.proj_y)))
        if self.state == "ANIM_MATURIN": 
            mx = Settings.SCREEN_WIDTH//2 - 200; my = Settings.SCREEN_HEIGHT//2 - 200
            screen.blit(self.maturin_img, (mx, my))

        self.draw_bar(screen, 50, 50, self.enemy_hp, self.enemy_max_hp, (200, 0, 0))
        self.draw_bar(screen, Settings.SCREEN_WIDTH - 250, 400, self.player_hp, self.player_max_hp, (0, 200, 0))
        
        panel = (0, Settings.SCREEN_HEIGHT - 150, Settings.SCREEN_WIDTH, 150)
        pygame.draw.rect(screen, Settings.COLOR_UI_BG, panel); pygame.draw.rect(screen, Settings.COLOR_UI_BORDER, panel, 4)
        screen.blit(self.font.render(self.message, True, Settings.COLOR_TEXT), (30, Settings.SCREEN_HEIGHT - 120))
        
        if self.state == "MENU":
            for i, opt in enumerate(self.options):
                c = Settings.COLOR_HIGHLIGHT if i == self.selected_index else (100, 100, 100)
                screen.blit(self.font.render(f"> {opt}", True, c), (30 + i * 180, Settings.SCREEN_HEIGHT - 60))
            screen.blit(self.font.render("[Z] Confirmar", True, (150,150,150)), (Settings.SCREEN_WIDTH-250, Settings.SCREEN_HEIGHT-30))

# ===== 3. DEFINIÇÃO DOS MAPAS =====

# --- MAPA 1: O ESGOTO PRINCIPAL (60x60) ---
MAPA_ESGOTO = [
    [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
    [1,0,0,1,2,2,2,2,2,1,1,1,2,2,2,2,2,2,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,2,2,2,2,2,2,2,2,2,2,2,2,2,1,1,1,1,1,1,1,1],
    [1,0,0,1,2,1,1,1,2,1,1,2,2,1,1,1,1,2,1,1,1,1,1,1,1,1,1,1,1,1,1,1,2,2,2,2,2,1,2,2,1,1,1,1,1,1,1,1,1,1,2,2,1,1,1,1,1,1,1,1],
    [1,0,0,2,2,1,1,1,2,2,2,2,1,1,1,1,1,2,2,1,1,1,1,1,1,1,1,1,1,1,1,2,2,1,1,1,2,2,2,1,1,1,1,1,1,1,1,1,1,1,1,2,1,1,1,1,1,1,1,1],
    [1,1,1,1,2,1,1,1,1,1,1,1,1,1,1,1,1,1,2,1,1,1,0,0,0,1,1,1,2,2,2,2,1,1,1,1,1,1,2,1,1,1,1,1,1,1,1,1,1,1,1,2,2,1,1,1,1,1,1,1],
    [1,1,1,1,2,1,1,1,1,1,1,1,1,1,1,1,1,1,2,2,1,0,0,0,0,0,1,2,2,1,1,1,1,1,1,1,1,1,2,1,1,1,1,1,1,1,2,2,2,2,1,1,2,1,1,1,1,1,1,1],
    [1,1,2,2,2,2,2,2,2,2,2,2,2,2,1,1,1,1,1,2,1,0,0,1,0,0,1,2,1,1,1,1,1,1,1,1,1,1,2,2,2,2,2,2,2,2,2,1,1,2,1,1,2,2,2,2,2,2,2,1],
    [1,1,2,1,1,1,1,1,1,1,1,1,1,2,1,1,1,1,1,2,1,1,1,1,1,1,1,2,1,1,1,1,1,1,1,2,2,2,2,1,1,1,1,1,1,1,1,1,1,2,1,1,1,1,1,1,1,1,2,1],
    [1,1,2,1,1,1,1,1,1,1,1,1,1,2,1,1,1,1,1,2,1,1,1,1,1,1,1,2,1,1,1,1,1,1,2,2,1,1,1,1,1,1,1,1,1,1,1,1,1,2,2,2,2,2,2,2,1,1,2,1],
    [1,1,2,1,1,1,1,2,2,2,2,2,1,2,1,1,1,2,2,2,2,2,2,2,2,2,2,2,1,1,1,1,1,2,2,1,1,1,1,1,1,1,1,1,1,1,3,3,3,3,1,1,1,1,1,2,1,1,2,1],
    [1,1,2,1,1,1,2,2,1,1,1,2,1,2,1,1,1,2,1,1,1,1,1,1,1,1,1,1,1,1,1,1,2,2,1,1,1,1,1,1,1,1,1,1,3,3,3,2,2,3,3,3,1,1,2,1,1,2,1],
    [1,1,2,1,1,2,2,1,1,1,1,2,2,2,1,1,1,2,1,1,1,1,1,1,1,1,1,1,1,1,1,2,2,1,1,1,1,1,1,1,1,1,1,3,3,2,2,2,2,2,2,3,3,1,2,1,1,2,1],
    [1,1,2,2,2,2,1,1,1,1,1,1,1,1,1,1,1,2,1,1,1,1,1,2,2,2,2,2,2,2,2,2,1,1,1,1,1,1,1,1,1,1,3,3,2,2,3,3,3,3,2,2,3,3,1,2,1,1,2,1],
    [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,2,1,1,1,1,1,2,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,3,3,2,2,3,1,1,1,1,3,2,2,3,1,2,2,2,2,1],
    [1,2,2,2,2,2,2,2,2,2,2,2,2,2,1,1,1,2,1,1,1,1,1,2,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,3,3,2,2,3,1,1,1,1,1,1,3,2,2,3,1,1,1,1,1],
    [1,2,1,1,1,1,1,1,1,1,1,1,1,2,1,1,1,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,1,1,1,1,1,1,3,3,2,2,3,1,1,1,1,1,1,1,1,3,2,3,3,1,1,1,1],
    [1,2,1,1,1,1,1,1,1,1,1,1,1,2,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,2,1,1,1,1,1,1,3,3,2,2,3,3,1,1,1,2,2,2,1,1,3,2,2,3,1,1,1,1],
    [1,2,1,1,1,1,2,2,2,2,2,1,1,2,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,2,1,1,1,1,1,1,3,2,2,3,1,1,1,2,2,1,2,2,1,1,3,2,3,1,1,1,1],
    [1,2,1,1,1,2,2,1,1,1,2,2,1,2,1,1,1,1,1,2,2,2,2,2,2,2,1,1,2,2,2,2,2,1,1,1,1,1,1,3,2,2,3,1,1,2,2,1,1,1,2,2,1,3,2,3,1,1,1,1],
    [1,2,1,1,2,2,1,1,1,1,1,2,2,2,1,1,1,1,1,2,1,1,1,1,1,2,1,1,2,1,1,1,1,1,1,1,1,1,1,3,3,2,3,1,1,2,1,1,1,1,1,2,1,3,2,3,1,1,1,1],
    [1,2,2,2,2,1,1,1,1,1,1,1,1,1,1,1,1,1,1,2,1,1,1,1,1,2,1,1,2,1,1,1,1,1,1,1,1,1,1,1,3,2,3,1,2,2,1,1,1,1,1,2,1,3,2,3,1,1,1,1],
    [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,2,1,1,1,1,1,2,1,1,2,2,2,2,2,2,2,2,2,1,1,1,3,2,3,1,2,1,1,1,1,1,1,2,1,3,2,3,1,1,1,1],
    [1,1,1,1,1,1,1,1,1,2,2,2,2,2,2,2,2,2,1,2,1,1,1,1,1,2,1,1,1,1,1,1,1,1,1,1,2,1,1,1,3,2,3,1,2,1,1,1,1,1,1,2,1,3,2,3,1,1,1,1],
    [1,2,2,2,2,2,2,2,2,2,1,1,1,1,1,1,1,2,1,2,1,1,1,1,1,2,2,2,2,2,2,2,2,2,2,1,2,1,1,3,3,2,3,3,2,1,1,1,1,1,1,2,1,3,2,3,1,1,1,1],
    [1,2,1,1,1,1,1,1,1,1,1,1,0,0,0,0,1,2,1,2,1,1,1,1,1,1,1,1,1,1,1,1,1,1,2,1,2,1,1,3,2,2,2,3,2,2,2,2,2,2,2,2,1,3,2,3,1,1,1,1],
    [1,2,1,1,1,1,1,1,1,1,1,1,0,0,0,0,1,2,1,2,1,1,1,1,1,1,1,1,1,1,1,1,1,1,2,1,2,1,1,3,2,2,2,3,3,3,3,3,3,3,3,3,1,3,2,3,1,1,1,1],
    [1,2,1,1,1,2,2,2,2,2,2,2,2,2,2,2,2,2,1,2,1,1,1,1,1,2,2,2,2,2,2,2,1,1,2,1,2,1,1,3,3,2,2,2,2,2,2,2,2,2,2,3,3,3,2,3,1,1,1,1],
    [1,2,1,1,1,2,1,1,1,1,1,1,1,1,1,1,1,1,1,2,1,1,1,1,1,2,1,1,1,1,1,2,1,1,2,2,2,1,1,1,3,3,3,3,3,3,3,3,3,3,2,3,2,2,2,3,1,1,1,1],
    [1,2,2,2,1,2,1,1,1,1,1,1,1,1,1,1,1,1,1,2,2,2,2,2,1,2,1,1,1,1,1,2,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,3,2,3,2,1,1,1,1,1,1,1],
    [1,1,1,2,1,2,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,2,1,2,1,1,1,1,1,2,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,3,2,3,2,1,1,1,1,1,1,1],
    [1,1,1,2,1,2,1,1,2,2,2,2,2,2,2,2,2,2,2,2,2,1,1,2,1,2,1,1,1,1,1,2,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,3,2,3,2,1,1,1,1,1,1,1],
    [1,1,1,2,1,2,1,1,2,1,1,1,1,1,1,1,1,1,1,1,2,1,1,2,2,2,1,1,1,1,1,2,2,2,2,2,2,2,1,1,1,1,1,1,1,1,1,1,3,2,3,2,1,1,1,1,1,1,1],
    [1,1,1,2,1,2,1,1,2,1,1,1,1,1,1,1,1,1,1,1,2,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,2,1,1,1,1,1,1,2,2,2,2,2,3,2,3,2,3,3,3,3,3,3,1],
    [1,1,1,2,2,2,1,1,2,2,2,2,2,2,2,1,1,1,1,1,2,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,2,1,1,1,1,1,1,2,1,1,1,1,3,2,3,2,3,2,2,2,2,3,1],
    [1,1,1,1,1,1,1,1,1,1,1,1,1,1,2,1,1,1,1,1,2,2,2,2,2,2,2,2,2,2,1,1,1,1,1,1,1,2,1,1,1,1,1,1,2,1,1,1,1,3,2,3,3,3,2,3,3,2,3,1],
    [1,2,2,2,2,2,2,2,2,2,2,2,2,1,2,1,1,1,1,1,1,1,1,1,1,1,1,1,1,2,1,1,1,1,1,1,1,2,2,2,2,2,2,2,2,1,1,1,1,3,2,2,2,2,2,3,3,2,3,1],
    [1,2,1,1,1,1,1,1,1,1,1,1,2,1,2,1,1,1,2,2,2,2,2,2,2,1,1,1,1,2,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,3,3,3,3,3,3,3,3,2,3,1],
    [1,2,1,1,1,1,1,1,1,1,1,1,2,1,2,1,1,1,2,1,1,1,1,1,2,1,1,1,1,2,1,1,2,2,2,2,2,2,2,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,2,3,1],
    [1,2,2,2,2,2,2,1,1,2,2,2,2,1,2,1,1,1,2,1,1,1,1,1,2,1,1,1,1,2,1,1,2,1,1,1,1,1,2,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,2,3,1],
    [1,1,1,1,1,1,2,1,1,2,1,1,1,1,2,1,1,1,2,2,2,2,1,1,2,2,2,2,1,2,1,1,2,1,1,1,1,1,2,1,1,1,1,1,2,2,2,2,2,2,2,2,2,2,2,2,2,2,3,1],
    [1,0,0,0,0,1,2,1,1,2,1,1,1,1,2,1,1,1,1,1,1,2,1,1,1,1,1,2,1,2,1,1,2,2,2,2,2,1,2,1,1,1,1,1,2,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
    [1,0,0,0,0,1,2,2,2,2,1,1,1,1,2,1,1,1,1,1,1,2,1,1,1,1,1,2,1,2,1,1,1,1,1,1,2,1,2,1,1,1,1,1,2,1,1,0,0,0,0,0,0,0,0,0,1,1,1,1],
    [1,1,1,1,1,1,1,1,1,1,1,1,1,1,2,2,2,2,2,2,2,2,1,1,1,1,1,2,2,2,1,1,1,1,1,1,2,1,2,1,1,1,1,1,2,1,1,0,0,0,0,0,0,0,0,0,1,1,1,1],
    [1,2,2,2,2,2,2,2,2,2,2,2,2,2,2,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,2,1,2,2,2,2,2,1,2,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
    [1,2,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,2,1,1,1,1,1,2,1,2,1,1,1,1,1,1,1,3,3,3,3,3,3,3,1],
    [1,2,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,2,2,2,2,1,1,2,1,2,1,1,1,1,1,1,1,3,2,2,2,2,2,3,1],
    [1,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,1,1,2,1,1,2,1,2,2,2,2,2,2,2,2,3,2,3,3,3,2,3,1],
    [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,2,1,1,2,1,1,1,1,1,1,1,1,1,3,2,3,1,3,2,3,1],
    [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,2,2,2,2,1,1,1,1,1,1,1,1,1,3,2,3,1,3,2,3,1],
    [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,3,3,3,1,3,3,3,1],
]

# Aplica o salão central 5x5 no mapa do esgoto
CENTER_Y_MAIN, CENTER_X_MAIN = len(MAPA_ESGOTO) // 2, len(MAPA_ESGOTO[0]) // 2
RADIUS_FLOOR_MAIN = 2.5 
RADIUS_WALL_MAIN = 3.5   

for y in range(len(MAPA_ESGOTO)):
    for x in range(len(MAPA_ESGOTO[0])):
        dist_sq = (x - CENTER_X_MAIN)**2 + (y - CENTER_Y_MAIN)**2
        if dist_sq <= RADIUS_FLOOR_MAIN**2:
            MAPA_ESGOTO[y][x] = 2 
        elif dist_sq <= RADIUS_WALL_MAIN**2:
            if MAPA_ESGOTO[y][x] != 2: 
                MAPA_ESGOTO[y][x] = 3

# --- MAPA 2: O NOVO LABIRINTO INTERMEDIÁRIO (40x40) ---
MAPA_LABIRINTO = []
# Gera um labirinto fechado simples de 40x40
for y in range(40):
    row = []
    for x in range(40):
        if x == 0 or x == 39 or y == 0 or y == 39: row.append(1) # Borda
        elif x % 2 == 0 and y % 2 == 0: row.append(1) # Pilares
        else: row.append(0) # Chão escuro
    MAPA_LABIRINTO.append(row)

# Abre o centro do Labirinto para o Poço 2
for y in range(18, 23):
    for x in range(18, 23):
        MAPA_LABIRINTO[y][x] = 2 # Chão claro

# --- MAPA 3: CORREDOR SUBINDO (FINAL) ---
def gerar_mapa_corredor_subida():
    width = 20
    height = 40
    mapa = [[9 for _ in range(width)] for _ in range(height)]
    center_x = width // 2
    start_y = 36
    room_center_y = 6

    # Corredor
    for y in range(start_y, room_center_y + 2, -1):
        mapa[y][center_x] = 7 
        mapa[y][center_x-1] = 8 
        mapa[y][center_x+1] = 8 

    # Sala Final 3x3
    room_radius = 3.0 
    wall_radius = 4.0
    
    for y in range(height):
        for x in range(width):
            dist = math.hypot(x - center_x, y - room_center_y)
            if dist <= room_radius:
                mapa[y][x] = 6 
            elif dist <= wall_radius:
                if mapa[y][x] != 7 and y <= room_center_y + 3:
                    mapa[y][x] = 8 
    
    mapa[start_y+1][center_x] = 8
    return mapa, center_x, start_y, room_center_y

MAPA_POCO, START_X_POCO, START_Y_POCO, IT_Y_POCO = gerar_mapa_corredor_subida()

# ===== 3. CLASSE CÂMERA =====
class Camera:
    def __init__(self, width, height):
        self.camera = pygame.Rect(0, 0, width, height)
        self.width = width
        self.height = height

    def apply(self, entity_rect):
        return entity_rect.move(self.camera.topleft)

    def update(self, target):
        x = -target.rect.centerx + int(Settings.SCREEN_WIDTH / 2)
        y = -target.rect.centery + int(Settings.SCREEN_HEIGHT / 2)
        x = min(0, max(-(self.width - Settings.SCREEN_WIDTH), x))
        y = min(0, max(-(self.height - Settings.SCREEN_HEIGHT), y))
        self.camera = pygame.Rect(x, y, self.width, self.height)

# ===== 4. CLASSE PENNYWISE (IT) =====
class Pennywise(pygame.sprite.Sprite):
    def __init__(self, x, y, image_path):
        super().__init__()
        try:
            img = pygame.image.load(image_path).convert_alpha()
        except pygame.error as e:
            print(f"Erro ao carregar IT: {e}")
            sys.exit()

        p_width = int(Settings.TILE_SIZE * 2.0)
        p_height = int(Settings.TILE_SIZE * 2.5)
        self.image = pygame.transform.scale(img, (p_width, p_height))
        self.rect = self.image.get_rect()
        
        self.rect.center = (x * Settings.TILE_SIZE + Settings.TILE_SIZE // 2, 
                            y * Settings.TILE_SIZE + Settings.TILE_SIZE // 2)

# ===== 5. GERENCIADOR DE OBJETOS =====
class ObjectHandler2D:
    def __init__(self, game):
        self.game = game 
        self.objects = []
        self.tex_stone = self.generate_stone_tex()
        self.tex_eyes = self.generate_eyes_tex()
        self.tex_well = self.generate_well_tex()
        
        self.total_stone_videos = 5 
        self.video_playlist = [f"pedra_{i}.mp4" for i in range(self.total_stone_videos)]
        random.shuffle(self.video_playlist)
        self.input_cooldown = 0
        self.score = 0

    def generate_stone_tex(self):
        s = pygame.Surface((Settings.TILE_SIZE, Settings.TILE_SIZE), pygame.SRCALPHA)
        radius = int(Settings.TILE_SIZE * 0.2)
        center = (Settings.TILE_SIZE // 2, Settings.TILE_SIZE // 2)
        pygame.draw.circle(s, (150, 150, 150), center, radius) 
        pygame.draw.circle(s, (50, 50, 50), center, radius, 2)
        return s

    def generate_eyes_tex(self):
        s = pygame.Surface((Settings.TILE_SIZE, Settings.TILE_SIZE), pygame.SRCALPHA)
        eye_offset = int(Settings.TILE_SIZE * 0.15)
        eye_radius = int(Settings.TILE_SIZE * 0.08)
        center = (Settings.TILE_SIZE // 2, Settings.TILE_SIZE // 2)
        pygame.draw.circle(s, (255, 255, 0), (center[0]-eye_offset, center[1]), eye_radius)
        pygame.draw.circle(s, (255, 255, 0), (center[0]+eye_offset, center[1]), eye_radius)
        return s

    def generate_well_tex(self):
        s = pygame.Surface((Settings.TILE_SIZE, Settings.TILE_SIZE), pygame.SRCALPHA)
        center = (Settings.TILE_SIZE // 2, Settings.TILE_SIZE // 2)
        pygame.draw.circle(s, (100, 100, 100), center, int(Settings.TILE_SIZE * 0.4))
        pygame.draw.circle(s, (0, 0, 0), center, int(Settings.TILE_SIZE * 0.3))
        return s

    def populate(self, mapa_atual):
        self.objects = [] 
        rows = len(mapa_atual)
        cols = len(mapa_atual[0])
        
        # MAPA 0: ESGOTO (PEDRAS + POÇO 1)
        if self.game.mapa_atual_id == 0:
            well_rect = pygame.Rect(CENTER_X_MAIN * Settings.TILE_SIZE, CENTER_Y_MAIN * Settings.TILE_SIZE, Settings.TILE_SIZE, Settings.TILE_SIZE)
            self.objects.append({'type': 'well', 'rect': well_rect, 'visible': True})

            stone_count = 0
            for y in range(1, rows - 1):
                for x in range(1, cols - 1):
                    try:
                        if mapa_atual[y][x] in (0, 2):
                            walls = 0
                            colors_wall = (1, 3)
                            if mapa_atual[y-1][x] in colors_wall: walls += 1
                            if mapa_atual[y+1][x] in colors_wall: walls += 1
                            if mapa_atual[y][x-1] in colors_wall: walls += 1
                            if mapa_atual[y][x+1] in colors_wall: walls += 1
                            
                            if walls >= 3:
                                if x < 10 and y < 10: continue
                                dist_to_center = math.hypot(x - CENTER_X_MAIN, y - CENTER_Y_MAIN)
                                if dist_to_center < 1.5: continue 

                                rect = pygame.Rect(x * Settings.TILE_SIZE, y * Settings.TILE_SIZE, Settings.TILE_SIZE, Settings.TILE_SIZE)
                                v_name = f"pedra_{stone_count % self.total_stone_videos}.mp4"
                                self.objects.append({'type': 'stone', 'rect': rect, 'visible': True, 'video': v_name})
                                self.objects.append({'type': 'eyes', 'rect': rect, 'visible': False})
                                stone_count += 1
                    except IndexError:
                        continue
        
        # MAPA 1: LABIRINTO (POÇO 2 NO CENTRO)
        elif self.game.mapa_atual_id == 1:
            well_rect = pygame.Rect(20 * Settings.TILE_SIZE, 20 * Settings.TILE_SIZE, Settings.TILE_SIZE, Settings.TILE_SIZE)
            self.objects.append({'type': 'well', 'rect': well_rect, 'visible': True})
    
    def trigger_random_video(self):
        if not self.video_playlist:
             self.video_playlist = [f"pedra_{i}.mp4" for i in range(self.total_stone_videos)]
             random.shuffle(self.video_playlist)
        self.game.play_video(self.video_playlist.pop())

    def update(self, player_rect, dt):
        keys = pygame.key.get_pressed()
        if self.game.mapa_atual_id == 0:
            self.input_cooldown += dt
            if keys[pygame.K_v] and self.input_cooldown > 500:
                self.trigger_random_video()
                self.input_cooldown = 0
        
        if keys[pygame.K_e]:
            for obj in self.objects:
                if obj['visible']:
                    if player_rect.colliderect(obj['rect'].inflate(10, 10)):
                        if obj['type'] == 'stone':
                            obj['visible'] = False
                            self.score += 1
                            for eye in self.objects:
                                if eye['type'] == 'eyes' and eye['rect'] == obj['rect']:
                                    eye['visible'] = True
                            if 'video' in obj: self.game.play_video(obj['video'])
                        elif obj['type'] == 'well':
                            # Lógica para entrar no poço
                            self.game.enter_well()

    def draw(self, screen, camera):
        for obj in self.objects:
            if obj['visible']:
                rect_on_screen = camera.apply(obj['rect'])
                if -Settings.TILE_SIZE < rect_on_screen.x < Settings.SCREEN_WIDTH and -Settings.TILE_SIZE < rect_on_screen.y < Settings.SCREEN_HEIGHT:
                    if obj['type'] == 'stone':
                        screen.blit(self.tex_stone, rect_on_screen)
                    elif obj['type'] == 'eyes':
                        screen.blit(self.tex_eyes, rect_on_screen)
                    elif obj['type'] == 'well':
                        screen.blit(self.tex_well, rect_on_screen)

# ===== 6. CLASSE JOGADOR =====
class AnimatedPlayer(pygame.sprite.Sprite):
    def __init__(self, x, y, image_path):
        super().__init__()
        try:
            original_image = pygame.image.load(image_path).convert_alpha()
            colorkey = original_image.get_at((0, 0))
            original_image.set_colorkey(colorkey)
        except pygame.error as e:
            print(f"Erro: {e}")
            sys.exit()

        p_width = int(Settings.TILE_SIZE * 0.6) 
        p_height = int(Settings.TILE_SIZE * 0.9)
        self.base_image = pygame.transform.scale(original_image, (p_width, p_height))
        self.images = {
            'down': self.base_image,
            'up': self.base_image,
            'left': pygame.transform.flip(self.base_image, True, False),
            'right': self.base_image
        }
        self.image = self.images['down']
        self.rect = self.image.get_rect()
        self.speed = 9 
        self.vel_x = 0
        self.vel_y = 0
        self.direction = 'down'
        self.animation_timer = 0
        self.animation_speed = 150 
        self.walking_frame = 0
        self.is_walking = False
        self.set_pos(x, y)
        
        try:
            self.step_sound = pygame.mixer.Sound("passos.mp3")
            self.step_sound.set_volume(Settings.VOLUME)
        except:
            self.step_sound = None
        self.sound_playing = False

    def set_pos(self, x, y):
        self.rect.topleft = (x * Settings.TILE_SIZE + (Settings.TILE_SIZE - self.rect.width) // 2, 
                             y * Settings.TILE_SIZE + (Settings.TILE_SIZE - self.rect.height) // 2)

    def set_volume(self, volume):
        if self.step_sound:
            self.step_sound.set_volume(volume)

    def update(self, walls_rects, dt, pennywise_sprite=None):
        self.vel_x = 0
        self.vel_y = 0
        keys = pygame.key.get_pressed()
        
        self.is_walking = False
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.vel_x = -self.speed
            self.direction = 'left'
            self.is_walking = True
        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.vel_x = self.speed
            self.direction = 'right'
            self.is_walking = True
        elif keys[pygame.K_UP] or keys[pygame.K_w]:
            self.vel_y = -self.speed
            self.direction = 'up'
            self.is_walking = True
        elif keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self.vel_y = self.speed
            self.direction = 'down'
            self.is_walking = True

        if self.step_sound:
            if self.is_walking and not self.sound_playing:
                self.step_sound.play(loops=-1)
                self.sound_playing = True
            elif not self.is_walking and self.sound_playing:
                self.step_sound.stop()
                self.sound_playing = False

        self.image = self.images[self.direction]
        if self.is_walking:
            self.animation_timer += dt
            if self.animation_timer >= self.animation_speed:
                self.animation_timer = 0
                self.walking_frame = (self.walking_frame + 1) % 2
            if self.walking_frame == 1:
                 offset = 6 
                 self.image = pygame.Surface(self.rect.size, pygame.SRCALPHA)
                 self.image.blit(self.images[self.direction], (0, -offset))
        else:
            self.walking_frame = 0
            self.animation_timer = 0

        collidables = list(walls_rects)
        
        self.rect.x += self.vel_x
        for obstacle in collidables:
            if self.rect.colliderect(obstacle):
                if self.vel_x > 0: self.rect.right = obstacle.left
                if self.vel_x < 0: self.rect.left = obstacle.right

        self.rect.y += self.vel_y
        for obstacle in collidables:
            if self.rect.colliderect(obstacle):
                if self.vel_y > 0: self.rect.bottom = obstacle.top
                if self.vel_y < 0: self.rect.top = obstacle.bottom

# ===== 7. JOGO PRINCIPAL =====
class Game:
    def __init__(self):
        self.cleanup_temp_files()
        Settings.SCREEN_WIDTH = 800; Settings.SCREEN_HEIGHT = 600
        self.screen = pygame.display.set_mode((Settings.SCREEN_WIDTH, Settings.SCREEN_HEIGHT), pygame.RESIZABLE)
        pygame.display.set_caption("Derry Sewers 2D - FINAL")
        self.clock = pygame.time.Clock()
        self.player = AnimatedPlayer(4, 2, "image_9.png")
        self.obj_handler = ObjectHandler2D(self)
        self.pennywise = None 
        self.battle = BattleSystem(self)
        self.state = "EXPLORING"
        
        self.font_ui = pygame.font.SysFont("Arial", 24, bold=True)

        try:
            self.wall_texture = pygame.image.load("image_24.png").convert()
            self.wall_texture = pygame.transform.scale(self.wall_texture, (Settings.TILE_SIZE, Settings.TILE_SIZE))
        except pygame.error as e:
            print(f"AVISO: Textura de parede 'image_24.png' não encontrada.")
            self.wall_texture = None
        
        self.mapa_atual_id = 0 
        self.load_map(MAPA_ESGOTO)

    def cleanup_temp_files(self):
        try:
            for f in glob.glob("temp_*.mp3"):
                try: os.remove(f)
                except: pass
        except: pass

    def play_video(self, filename):
        if not HAS_MOVIEPY: return
        if not os.path.exists(filename):
            print(f"AVISO: Vídeo '{filename}' não encontrado.")
            return

        try:
            pygame.mixer.music.pause()
            if self.player.step_sound: self.player.step_sound.stop()
            clip = VideoFileClip(filename)
            audio_filename = f"temp_audio_{random.randint(1000, 9999)}.mp3"
            if clip.audio:
                try:
                    clip.audio.write_audiofile(audio_filename, logger=None)
                    pygame.mixer.music.load(audio_filename)
                    pygame.mixer.music.play()
                except: pass
            running = True
            for frame in clip.iter_frames(fps=Settings.FPS, dtype="uint8"):
                if not running: break
                for event in pygame.event.get():
                    if event.type == pygame.QUIT: pygame.quit(); sys.exit()
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_SPACE or event.key == pygame.K_ESCAPE:
                            running = False
                            pygame.mixer.music.stop()

                frame_surf = pygame.surfarray.make_surface(frame.swapaxes(0, 1))
                frame_surf = pygame.transform.scale(frame_surf, self.screen.get_size())
                self.screen.blit(frame_surf, (0, 0))
                pygame.display.flip()
                self.clock.tick(Settings.FPS)
            
            if clip.audio:
                pygame.mixer.music.stop()
                pygame.mixer.music.unload()
                try: 
                    clip.close()
                    if os.path.exists(audio_filename): os.remove(audio_filename)
                except: pass
            
            if self.state == "EXPLORING" and self.mapa_atual_id == 0: self.play_game_music()
                
        except Exception as e:
            print(f"Erro vídeo: {e}")

    def play_intro(self): self.play_video("intro.mp4")
    def play_scene1(self): self.play_video("cena1.mp4")
    def play_game_music(self):
        if os.path.exists("sound.mp3"):
            try:
                pygame.mixer.music.load("sound.mp3")
                pygame.mixer.music.set_volume(Settings.VOLUME)
                pygame.mixer.music.play(loops=-1)
            except: pass
        else:
            print("AVISO: 'sound.mp3' não encontrado.")

    def change_volume(self, change):
        Settings.VOLUME = max(0.0, min(1.0, Settings.VOLUME + change))
        try: pygame.mixer.music.set_volume(Settings.VOLUME)
        except: pass
        self.player.set_volume(Settings.VOLUME)

    def load_map(self, mapa_data):
        self.walls = []
        self.floor_tiles = []
        self.pennywise = None 
        
        rows = len(mapa_data)
        cols = len(mapa_data[0])
        map_pixel_width = cols * Settings.TILE_SIZE
        map_pixel_height = rows * Settings.TILE_SIZE
        
        for row, tiles in enumerate(mapa_data):
            for col, tile in enumerate(tiles):
                rect = pygame.Rect(col * Settings.TILE_SIZE, row * Settings.TILE_SIZE, Settings.TILE_SIZE, Settings.TILE_SIZE)
                
                if tile == 1: self.walls.append({'rect': rect, 'color': Settings.COLOR_WALL})
                elif tile == 3: self.walls.append({'rect': rect, 'color': Settings.COLOR_WALL_3})
                elif tile == 2: self.floor_tiles.append({'rect': rect, 'color': Settings.COLOR_FLOOR})
                elif tile == 0: self.floor_tiles.append({'rect': rect, 'color': (35, 35, 35)})
                elif tile == 8: self.walls.append({'rect': rect, 'color': Settings.COLOR_WELL_WALL})
                elif tile == 7: self.floor_tiles.append({'rect': rect, 'color': Settings.COLOR_WELL_FLOOR})
                elif tile == 6: self.floor_tiles.append({'rect': rect, 'color': Settings.COLOR_WELL_CRACKED})
        
        self.camera = Camera(map_pixel_width, map_pixel_height)
        self.obj_handler.populate(mapa_data)

    def enter_well(self):
        # Lógica de transição de mapas
        if self.mapa_atual_id == 0:
            if self.obj_handler.score >= 5:
                self.mapa_atual_id = 1 # Vai para o Labirinto
                self.load_map(MAPA_LABIRINTO)
                self.player.set_pos(2, 2) # Início do labirinto
            else:
                print(f"PRECISA DE 5 PEDRAS! (VOCÊ TEM {self.obj_handler.score})")
        
        elif self.mapa_atual_id == 1:
            self.mapa_atual_id = 2 # Vai para o Corredor do IT
            self.load_map(MAPA_POCO)
            self.player.set_pos(START_X_POCO, START_Y_POCO) 
            self.pennywise = Pennywise(START_X_POCO, IT_Y_POCO, "image_17.png")

    def show_start_screen(self):
        bg_image = None
        try:
            bg_image = pygame.image.load("image_16.png").convert()
        except (FileNotFoundError, pygame.error):
            print("AVISO: Imagem de fundo 'image_16.png' não encontrada.")
            bg_image = pygame.Surface((Settings.SCREEN_WIDTH, Settings.SCREEN_HEIGHT))
            bg_image.fill((0, 0, 0))

        font = pygame.font.SysFont(None, 50)
        text = font.render("Iniciar Jogo", True, (255, 255, 255))
        button_rect = pygame.Rect(0, 0, 250, 60)
        button_rect.center = (Settings.SCREEN_WIDTH // 2, Settings.SCREEN_HEIGHT - 100)

        waiting_for_start = True
        while waiting_for_start:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1 and button_rect.collidepoint(event.pos):
                        waiting_for_start = False
                if event.type == pygame.VIDEORESIZE:
                    Settings.SCREEN_WIDTH = event.w
                    Settings.SCREEN_HEIGHT = event.h
                    self.screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
                    button_rect.center = (Settings.SCREEN_WIDTH // 2, Settings.SCREEN_HEIGHT - 100)
                    if bg_image:
                        bg_image = pygame.transform.scale(bg_image, (Settings.SCREEN_WIDTH, Settings.SCREEN_HEIGHT))

            if bg_image:
                current_bg = pygame.transform.scale(bg_image, (Settings.SCREEN_WIDTH, Settings.SCREEN_HEIGHT))
                self.screen.blit(current_bg, (0, 0))
            else:
                self.screen.fill((0,0,0))

            pygame.draw.rect(self.screen, (200, 50, 50), button_rect) 
            pygame.draw.rect(self.screen, (255, 255, 255), button_rect, 2) 
            text_rect = text.get_rect(center=button_rect.center)
            self.screen.blit(text, text_rect)
            
            pygame.display.flip()
            self.clock.tick(Settings.FPS)

    def run(self):
        self.play_intro()
        self.show_start_screen()
        self.play_scene1()
        self.play_game_music()
        
        while True:
            dt = self.clock.tick(Settings.FPS)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        pygame.quit(); sys.exit()
                    if event.key == pygame.K_PLUS or event.key == pygame.K_KP_PLUS or event.key == pygame.K_EQUALS:
                        self.change_volume(0.1)
                    if event.key == pygame.K_MINUS or event.key == pygame.K_KP_MINUS:
                        self.change_volume(-0.1)
                    if event.key == pygame.K_v and self.mapa_atual_id == 0: self.obj_handler.trigger_random_video()
                    
                    # CHEAT TELEPORTE (K) - ATUALIZADO PARA CADA MAPA
                    if event.key == pygame.K_k:
                        if self.mapa_atual_id == 0:
                             # Lado do Poço 1
                             self.player.rect.center = (32 * Settings.TILE_SIZE, 30 * Settings.TILE_SIZE)
                        elif self.mapa_atual_id == 1:
                             # Lado do Poço 2 (Centro do labirinto)
                             self.player.rect.center = (22 * Settings.TILE_SIZE, 20 * Settings.TILE_SIZE)
                        elif self.mapa_atual_id == 2:
                             # Perto do IT
                             self.player.rect.center = (START_X_POCO * Settings.TILE_SIZE, IT_Y_POCO * Settings.TILE_SIZE + 200)

                    # CHEAT P = +5 PEDRAS ou SAIR
                    if event.key == pygame.K_p:
                        if self.state == "BATTLING" and self.battle.state == "WIN":
                             self.play_video("exit.mp4")
                             pygame.quit(); sys.exit()
                        elif self.state == "EXPLORING":
                             self.obj_handler.score = 5
                             print("CHEAT: +5 PEDRAS ADICIONADAS!")

                if event.type == pygame.VIDEORESIZE:
                    Settings.SCREEN_WIDTH = event.w
                    Settings.SCREEN_HEIGHT = event.h
                    self.screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)

            if self.state == "EXPLORING":
                wall_rects = [w['rect'] for w in self.walls]
                current_it = self.pennywise if self.mapa_atual_id == 2 else None # IT só aparece no mapa 2
                self.player.update(wall_rects, dt, current_it)
                self.obj_handler.update(self.player.rect, dt)
                self.camera.update(self.player)
                
                # TRIGGER BATALHA
                if current_it and self.player.rect.colliderect(current_it.rect.inflate(-20,-20)):
                    self.state = "BATTLING"
                    self.battle.start_battle()
                    pygame.mixer.music.stop()

                self.screen.fill(Settings.COLOR_BG)
                for t in self.floor_tiles:
                    rs = self.camera.apply(pygame.Rect(t['rect']))
                    if -Settings.TILE_SIZE < rs.x < Settings.SCREEN_WIDTH: pygame.draw.rect(self.screen, t['color'], rs)
                self.obj_handler.draw(self.screen, self.camera)
                for w in self.walls:
                    rs = self.camera.apply(pygame.Rect(w['rect']))
                    if -Settings.TILE_SIZE < rs.x < Settings.SCREEN_WIDTH:
                        if self.wall_texture: self.screen.blit(self.wall_texture, rs)
                        else: pygame.draw.rect(self.screen, (100,100,100), rs)
                if self.pennywise: self.screen.blit(self.pennywise.image, self.camera.apply(self.pennywise.rect))
                self.screen.blit(self.player.image, self.camera.apply(self.player.rect))
                
            elif self.state == "BATTLING":
                self.battle.update()
                self.battle.draw(self.screen)

            # UI Volume + Score
            self.screen.blit(self.font_ui.render(f"VOL: {int(Settings.VOLUME*100)}%", True, (255,255,255)), (10,10))
            self.screen.blit(self.font_ui.render(f"PEDRAS: {self.obj_handler.score}", True, (255,255,255)), (10,40))
            
            pygame.display.flip()

if __name__ == "__main__":
    game = Game()
    game.run()