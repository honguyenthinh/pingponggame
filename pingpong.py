import pygame, sys, random, math, cv2
import mediapipe as mp

# ================= CONFIG =================
SCREEN_W, SCREEN_H = 640, 480
FPS = 60

PADDLE_W, PADDLE_H = 140, 18
BALL_R = 10

BRICK_COLS = 8
BRICK_H = 22
BRICK_GAP = 4
BRICK_TOP = 60

LIVES = 3
MAX_LEVEL = 3

WHITE = (255,255,255)
GRAY  = (180,180,180)
BLACK = (0,0,0)
BG    = (15,18,22)
GREEN = (120,255,120)

COLORS = [
    (255,99,71),(255,215,0),(135,206,235),
    (218,112,214),(144,238,144)
]

# ================= UTILS =================
def clamp(v,a,b): return max(a,min(v,b))
def lerp(a,b,t): return a+(b-a)*t

def circle_rect(cx,cy,r,rect):
    nx = clamp(cx,rect.left,rect.right)
    ny = clamp(cy,rect.top,rect.bottom)
    return (cx-nx)**2+(cy-ny)**2 <= r*r

# ================= OBJECTS =================
class Paddle:
    def __init__(self):
        self.w,self.h = PADDLE_W,PADDLE_H
        self.x = SCREEN_W//2-self.w//2
        self.y = SCREEN_H-80

    def rect(self):
        return pygame.Rect(int(self.x),int(self.y),self.w,self.h)

    def move(self,x,y):
        self.x = clamp(x,0,SCREEN_W-self.w)
        self.y = clamp(y,BRICK_TOP+120,SCREEN_H-self.h-10)

    def draw(self,s):
        pygame.draw.rect(s,WHITE,self.rect(),border_radius=8)

class Ball:
    def __init__(self,level):
        self.level = level
        self.reset()

    def reset(self):
        self.x,self.y = SCREEN_W//2,SCREEN_H//2
        speed = 5 + self.level
        angle = random.uniform(-0.9,0.9)
        self.vx = math.sin(angle)*speed
        self.vy = -abs(math.cos(angle)*speed)

    def update(self):
        self.x += self.vx
        self.y += self.vy

    def draw(self,s):
        pygame.draw.circle(s,WHITE,(int(self.x),int(self.y)),BALL_R)

class Brick:
    def __init__(self,x,y,w,h,c):
        self.rect = pygame.Rect(x,y,w,h)
        self.color = c

    def draw(self,s):
        pygame.draw.rect(s,self.color,self.rect)
        pygame.draw.rect(s,BLACK,self.rect,2)

class FloatingText:
    def __init__(self,x,y,text):
        self.x,self.y = x,y
        self.text = text
        self.life = 30

    def update(self):
        self.y -= 1
        self.life -= 1

    def draw(self,s,font):
        if self.life > 0:
            img = font.render(self.text,True,GREEN)
            s.blit(img,(self.x,self.y))

# ================= CAMERA =================
class Camera:
    def __init__(self):
        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, SCREEN_W)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, SCREEN_H)

        self.face = mp.solutions.face_mesh.FaceMesh(max_num_faces=1)
        self.last = (0.5,0.7)
        self.smooth = 0.35

    def read(self):
        ok,frame = self.cap.read()
        if not ok:
            return None,None
        frame = cv2.flip(frame,1)
        rgb = cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)
        res = self.face.process(rgb)

        if res.multi_face_landmarks:
            nose = res.multi_face_landmarks[0].landmark[1]
            x = lerp(self.last[0],nose.x,self.smooth)
            y = lerp(self.last[1],nose.y,self.smooth)
            self.last = (x,y)
            return (x,y), frame

        return None, frame

# ================= BUILD =================
def build_bricks(level):
    bricks=[]
    rows = 3 + level
    bw=(SCREEN_W-20)//BRICK_COLS
    for r in range(rows):
        for c in range(BRICK_COLS):
            x=10+c*bw
            y=BRICK_TOP+r*(BRICK_H+BRICK_GAP)
            bricks.append(
                Brick(x,y,bw-BRICK_GAP,BRICK_H,COLORS[(r+c)%5])
            )
    return bricks

# ================= INIT =================
pygame.init()
screen = pygame.display.set_mode((SCREEN_W,SCREEN_H))
pygame.display.set_caption("Ping Pong - Nose Control")

clock = pygame.time.Clock()
font = pygame.font.SysFont(None,24)
big  = pygame.font.SysFont(None,52)

cam = Camera()

def message_screen(title,sub):
    while True:
        screen.fill(BG)
        t = big.render(title,True,WHITE)
        s = font.render(sub,True,GRAY)
        screen.blit(t,(SCREEN_W//2-t.get_width()//2,170))
        screen.blit(s,(SCREEN_W//2-s.get_width()//2,240))
        pygame.display.flip()
        for e in pygame.event.get():
            if e.type==pygame.QUIT: sys.exit()
            if e.type==pygame.KEYDOWN:
                if e.key==pygame.K_SPACE: return
                if e.key==pygame.K_ESCAPE: sys.exit()

# ================= START =================
level = 1
message_screen("PING PONG", "Move NOSE | SPACE start | ESC exit")

# ================= GAME LOOP =================
while True:
    paddle = Paddle()
    ball = Ball(level)
    bricks = build_bricks(level)
    texts=[]
    lives=LIVES
    score=0
    playing=True

    while playing:
        clock.tick(FPS)

        for e in pygame.event.get():
            if e.type==pygame.QUIT: sys.exit()
            if e.type==pygame.KEYDOWN and e.key==pygame.K_ESCAPE:
                sys.exit()

        # CAMERA
        norm, frame = cam.read()
        if norm:
            paddle.move(
                norm[0]*SCREEN_W-paddle.w/2,
                norm[1]*SCREEN_H-paddle.h/2
            )

        ball.update()
        speed = math.hypot(ball.vx,ball.vy)

        # WALLS
        if ball.x-BALL_R<=0 or ball.x+BALL_R>=SCREEN_W:
            ball.vx*=-1
        if ball.y-BALL_R<=0:
            ball.vy=abs(ball.vy)

        # PADDLE
        if circle_rect(ball.x,ball.y,BALL_R,paddle.rect()) and ball.vy>0:
            hit = (ball.x-paddle.rect().centerx)/(paddle.w/2)
            hit = clamp(hit,-1,1)
            angle = hit*math.radians(60)
            ball.vx = speed*math.sin(angle)
            ball.vy = -speed*math.cos(angle)
            ball.y = paddle.rect().top-BALL_R-1

        # BRICKS
        for b in bricks[:]:
            if circle_rect(ball.x,ball.y,BALL_R,b.rect):
                cx = clamp(ball.x,b.rect.left,b.rect.right)
                cy = clamp(ball.y,b.rect.top,b.rect.bottom)
                if abs(ball.x-cx)>abs(ball.y-cy):
                    ball.vx*=-1
                else:
                    ball.vy*=-1
                bricks.remove(b)
                score+=10
                texts.append(FloatingText(b.rect.centerx,b.rect.centery,"+10"))
                break

        # LOSE BALL
        if ball.y-BALL_R>SCREEN_H:
            lives-=1
            ball.reset()
            if lives<=0:
                playing=False
                level=1
                message_screen("GAME OVER", "SPACE restart")

        # WIN LEVEL
        if not bricks:
            playing=False
            level+=1
            if level>MAX_LEVEL:
                message_screen("YOU WIN 🎉", "SPACE restart")
                level=1
            else:
                message_screen(f"LEVEL {level}", "SPACE continue")

        # DRAW
        if frame is not None:
            bg = cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)
            surf = pygame.image.frombuffer(bg.tobytes(),(SCREEN_W,SCREEN_H),"RGB")
            screen.blit(surf,(0,0))
        else:
            screen.fill(BG)

        # DRAW BRICKS, PADDLE, BALL
        for b in bricks: b.draw(screen)
        paddle.draw(screen)
        ball.draw(screen)

        # DRAW +10 FLOATING TEXTS
        for t in texts[:]:
            t.update()
            t.draw(screen,font)
            if t.life<=0: texts.remove(t)

        # HUD với khung điểm
        hud_text = f"Score {score}   Lives {lives}   Level {level}"
        hud = font.render(hud_text,True,WHITE)
        pygame.draw.rect(screen,BLACK,(5,5,hud.get_width()+10,hud.get_height()+6),0)
        screen.blit(hud,(10,8))

        pygame.display.flip()
