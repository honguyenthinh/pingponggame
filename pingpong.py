import pygame, sys, random, math, cv2
import mediapipe as mp

# ================= CONFIG =================
SCREEN_W, SCREEN_H = 640, 480
FPS = 60

PADDLE_W, PADDLE_H = 140, 18
BALL_R = 10

BRICK_COLS = 8
BRICK_ROWS = 5
BRICK_H = 22
BRICK_GAP = 4
BRICK_TOP = 60

LIVES = 3

WHITE = (255,255,255)
GRAY  = (180,180,180)
BLACK = (0,0,0)
BG    = (15,18,22)
GREEN = (120,255,120)

COLORS = [(255,99,71),(255,215,0),(135,206,235),
          (218,112,214),(144,238,144)]

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
        self.min_y = BRICK_TOP + BRICK_ROWS*(BRICK_H+BRICK_GAP) + 10

    def rect(self):
        return pygame.Rect(int(self.x),int(self.y),self.w,self.h)

    def move(self,x,y,bricks):
        nx = clamp(x,0,SCREEN_W-self.w)
        ny = clamp(y,self.min_y,SCREEN_H-self.h-10)
        test = pygame.Rect(nx,ny,self.w,self.h)
        for b in bricks:
            if test.colliderect(b.rect):
                return
        self.x,self.y = nx,ny

    def draw(self,s):
        pygame.draw.rect(s,WHITE,self.rect(),border_radius=8)

class Ball:
    def __init__(self):
        self.reset()

    def reset(self):
        self.x,self.y = SCREEN_W//2,SCREEN_H//2
        ang = random.uniform(-0.6,0.6)
        self.vx = math.sin(ang)*6
        self.vy = -abs(math.cos(ang)*6)

    def update(self):
        self.x+=self.vx
        self.y+=self.vy

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

# ================= CAMERA (NOSE) =================
class Camera:
    def __init__(self):
        self.cap = cv2.VideoCapture(0)
        self.cap.set(3,SCREEN_W)
        self.cap.set(4,SCREEN_H)

        self.face = mp.solutions.face_mesh.FaceMesh(
            max_num_faces=1,
            min_detection_confidence=0.6,
            min_tracking_confidence=0.6
        )

        self.last = (0.5,0.7)
        self.smooth = 0.5

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
def build_bricks():
    bricks=[]
    bw=(SCREEN_W-20)//BRICK_COLS
    for r in range(BRICK_ROWS):
        for c in range(BRICK_COLS):
            x=10+c*bw
            y=BRICK_TOP+r*(BRICK_H+BRICK_GAP)
            bricks.append(Brick(x,y,bw-BRICK_GAP,BRICK_H,COLORS[(r+c)%5]))
    return bricks

# ================= MAIN =================
pygame.init()
screen = pygame.display.set_mode((SCREEN_W,SCREEN_H))
pygame.display.set_caption("Ping Pong - Nose Control")
clock = pygame.time.Clock()
font = pygame.font.SysFont(None,24)
big  = pygame.font.SysFont(None,44)

cam = Camera()

def start_screen():
    while True:
        screen.fill(BG)
        t = big.render("PING PONG - NOSE CONTROL",True,WHITE)
        screen.blit(t,(SCREEN_W//2-t.get_width()//2,150))
        s = font.render("Move your NOSE | SPACE start | ESC exit",True,GRAY)
        screen.blit(s,(SCREEN_W//2-s.get_width()//2,220))
        pygame.display.flip()
        for e in pygame.event.get():
            if e.type==pygame.QUIT: sys.exit()
            if e.type==pygame.KEYDOWN:
                if e.key==pygame.K_SPACE: return
                if e.key==pygame.K_ESCAPE: sys.exit()

start_screen()

paddle = Paddle()
ball = Ball()
bricks = build_bricks()
texts = []
lives = LIVES
score = 0
playing = False

# ================= LOOP =================
while True:
    clock.tick(FPS)

    for e in pygame.event.get():
        if e.type==pygame.QUIT: sys.exit()
        if e.type==pygame.KEYDOWN:
            if e.key==pygame.K_ESCAPE: sys.exit()
            if e.key==pygame.K_SPACE: playing=True

    norm, frame = cam.read()
    if norm:
        paddle.move(norm[0]*SCREEN_W-paddle.w/2,
                    norm[1]*SCREEN_H-paddle.h/2,
                    bricks)

    if playing:
        ball.update()

        if ball.x-BALL_R<=0 or ball.x+BALL_R>=SCREEN_W:
            ball.vx*=-1
        if ball.y-BALL_R<=0:
            dx = ball.x - b.rect.centerx
            ball.vx += dx * 0.03
            ball.vy *= -1


        if circle_rect(ball.x,ball.y,BALL_R,paddle.rect()):
            ball.vy = -abs(ball.vy)
            ball.y = paddle.y - BALL_R

        for b in bricks[:]:
            if circle_rect(ball.x,ball.y,BALL_R,b.rect):
                ball.vy*=-1
                bricks.remove(b)
                score += 10
                texts.append(FloatingText(b.rect.centerx,b.rect.centery,"+10"))
                break

        if ball.y>SCREEN_H:
            lives-=1
            playing=False
            ball.reset()
            if lives<=0:
                start_screen()
                lives=LIVES
                score=0
                bricks=build_bricks()

    if frame is not None:
        bg = cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)
        surf = pygame.image.frombuffer(bg.tobytes(),(SCREEN_W,SCREEN_H),"RGB")
        screen.blit(surf,(0,0))
    else:
        screen.fill(BG)

    for b in bricks: b.draw(screen)
    paddle.draw(screen)
    ball.draw(screen)

    pygame.draw.rect(screen,BLACK,(10,10,220,32))
    hud = font.render(f"Score: {score}   Lives: {lives}",True,WHITE)
    screen.blit(hud,(20,16))

    for t in texts[:]:
        t.update()
        t.draw(screen,font)
        if t.life<=0: texts.remove(t)

    if not playing:
        h = font.render("Press SPACE",True,GRAY)
        screen.blit(h,(SCREEN_W//2-h.get_width()//2,SCREEN_H-30))

    pygame.display.flip()
