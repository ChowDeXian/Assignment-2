# Import libraries
import pygame
import math
import heapq

# ------------------------ Map Definitions ------------------------ #
START    = 'S'
TREASURE = 'T'
BLOCKED  = '#'
TRAPS    = ['X1', 'X2', 'X3', 'X4']
REWARDS  = ['R1', 'R2']
EMPTY    = ''

grid = [
    ['', '', '', '', '', '', '', '', '', ''],
    ['S', 'X2', '', 'X4', 'R1', '', '', '', '', ''],
    ['', '', '', '', 'T', '', 'X3', 'R2', '#', ''],
    ['', 'R1', '#', '#', '#', 'X3', '', 'T', 'X1', 'T'],
    ['#', '', '', 'T', '', '', '#', '#', '', ''],
    ['', '', 'X2', '', '#', 'R2', '#', '', '', ''],
    ['', '', '', '', '', '', '', '', '', '']
]

ROWS, COLS = len(grid), len(grid[0])

TILE_SIZE = 40
HEX_H = TILE_SIZE * math.sqrt(3) / 2
WIDTH = int(COLS * TILE_SIZE * 0.75 + TILE_SIZE / 4)
HEIGHT = int(ROWS * HEX_H + HEX_H / 2 + 60 + 50)

COLORS = {
    START: (0, 100, 255),
    TREASURE: (255, 255, 0),
    BLOCKED: (80, 80, 80),
    'X1': (200, 100, 100),
    'X2': (180, 80, 120),
    'X3': (160, 60, 140),
    'X4': (140, 40, 160),
    'R1': (100, 255, 100),
    'R2': (100, 200, 255),
    EMPTY: (255, 255, 255),
    'PATH': (255, 165, 0)
}

TileInfo = {
    'X1': "Trap 1: Increases gravity — step costs double energy.",
    'X2': "Trap 2: Decreases speed — moves cost double steps.",
    'X3': "Trap 3: Pushes you two cells forward.",
    'X4': "Trap 4: Destroys all uncollected treasures.",
    'R1': "Reward 1: Decreases gravity — step costs half energy.",
    'R2': "Reward 2: Increases speed — moves cost half steps.",
    'T':  "Treasure! You found one!",
    '':   "Empty Tile",
    '#':  "Blocked Tile",
    'S':  "Start Position"
}

def hex_to_pixel(r, c):
    x = TILE_SIZE * 0.75 * c + TILE_SIZE / 2
    y = HEX_H * r + (HEX_H / 2 if c % 2 == 1 else 0) + HEX_H / 2
    return x, y

def pixel_to_hex(x, y):
    for r in range(ROWS):
        for c in range(COLS):
            hx, hy = hex_to_pixel(r, c)
            dist = math.hypot(hx - x, hy - y)
            if dist < TILE_SIZE / 2:
                return r, c
    return None, None

def hex_corners(x, y):
    return [
        (x + TILE_SIZE / 2 * math.cos(math.radians(angle)),
         y + TILE_SIZE / 2 * math.sin(math.radians(angle)))
        for angle in range(0, 360, 60)
    ]

def find_start():
    for r in range(ROWS):
        for c in range(COLS):
            if grid[r][c] == START:
                return r, c
    return 0, 0

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Hex Grid Treasure Hunt")
font = pygame.font.SysFont('Arial', 18)

health = 10
collected_treasures = set()
all_treasures = {(r, c) for r in range(ROWS) for c in range(COLS) if grid[r][c] == TREASURE}

def draw_grid(player_pos, path=[]):
    screen.fill((100, 100, 100))
    for r in range(ROWS):
        for c in range(COLS):
            x, y = hex_to_pixel(r, c)
            corners = hex_corners(x, y)
            tile = grid[r][c]
            color = COLORS.get(tile, COLORS[EMPTY])
            if (r, c) in path:
                color = COLORS['PATH']
            pygame.draw.polygon(screen, color, corners)
            pygame.draw.polygon(screen, (0, 0, 0), corners, 1)
            text = font.render(tile, True, (0, 0, 0))
            screen.blit(text, text.get_rect(center=(x, y)))
            if (r, c) == player_pos:
                pygame.draw.circle(screen, (0, 0, 0), (int(x), int(y)), 10)
    draw_legend()
    draw_status()

def draw_legend():
    y = HEIGHT - 45
    x = 30
    legend_items = [
        ('S = Start', COLORS[START]),
        ('T = Treasure', COLORS[TREASURE]),
        ('# = Blocked', COLORS[BLOCKED]),
        ('X1..X4 = Traps', (160, 60, 120)),
        ('R1..R2 = Rewards', (100, 200, 255)),
        ('. = Empty', COLORS[EMPTY]),
    ]
    for label, color in legend_items:
        pygame.draw.rect(screen, color, (x, y, 20, 20))
        pygame.draw.rect(screen, (0, 0, 0), (x, y, 20, 20), 1)
        text = font.render(label, True, (255, 255, 255))
        screen.blit(text, (x + 25, y))
        x += 150

def draw_status():
    status = f"Health: {health} | Treasures: {len(collected_treasures)}/{len(all_treasures)}"
    text = font.render(status, True, (255, 255, 255))
    screen.blit(text, (10, HEIGHT - 90))

def display_description(desc):
    pygame.draw.rect(screen, (30, 30, 30), (0, HEIGHT - 120, WIDTH, 25))
    text = font.render(desc, True, (255, 255, 255))
    rect = text.get_rect(center=(WIDTH // 2, HEIGHT - 110))
    screen.blit(text, rect)

def get_neighbors(r, c):
    even = (c % 2 == 0)
    dirs = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    dirs += [(-1 if even else 0, -1), (-1 if even else 0, 1)] if even else [(1, -1), (1, 1)]
    neighbors = []
    for dr, dc in dirs:
        nr, nc = r + dr, c + dc
        if 0 <= nr < ROWS and 0 <= nc < COLS and grid[nr][nc] != BLOCKED:
            neighbors.append((nr, nc))
    return neighbors

def heuristic(a, b):
    ax, ay = hex_to_pixel(*a)
    bx, by = hex_to_pixel(*b)
    return math.hypot(ax - bx, ay - by)

def a_star(start, goal):
    open_set = [(0, start)]
    came_from = {}
    g_score = {start: 0}

    while open_set:
        _, current = heapq.heappop(open_set)

        if current == goal:
            path = []
            while current in came_from:
                path.append(current)
                current = came_from[current]
            path.reverse()
            return path

        for neighbor in get_neighbors(*current):
            tile = grid[neighbor[0]][neighbor[1]]
            cost = 1
            if tile == 'X1': cost *= 2
            elif tile == 'X2': cost *= 2
            elif tile == 'X3': cost += 5
            elif tile == 'X4': cost += 10
            elif tile == 'R1': cost *= 0.5
            elif tile == 'R2': cost *= 0.5

            tentative_g = g_score[current] + cost
            if neighbor not in g_score or tentative_g < g_score[neighbor]:
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g
                f_score = tentative_g + heuristic(neighbor, goal)
                heapq.heappush(open_set, (f_score, neighbor))

    return []

def main():
    global health
    clock = pygame.time.Clock()
    player_r, player_c = find_start()
    path = []
    running = True

    while running:
        clock.tick(10)
        draw_grid((player_r, player_c), path)
        tile = grid[player_r][player_c]
        display_description(TileInfo.get(tile, "Nothing interesting here"))
        pygame.display.flip()

        if (player_r, player_c) in all_treasures:
            collected_treasures.add((player_r, player_c))

        if tile in TRAPS:
            health -= 1
        elif tile in REWARDS:
            health = min(health + 1, 10)

        if tile == 'X4':
            for r, c in list(all_treasures):
                if (r, c) not in collected_treasures:
                    grid[r][c] = ''
                    all_treasures.remove((r, c))

        if health <= 0 or collected_treasures == all_treasures:
            print("Game Over" if health <= 0 else "All Treasures Found!")
            pygame.time.wait(2000)
            running = False

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = pygame.mouse.get_pos()
                r, c = pixel_to_hex(mx, my)
                if r is not None and (r, c) != (player_r, player_c):
                    path = a_star((player_r, player_c), (r, c))
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and path:
                    player_r, player_c = path.pop(0)

        keys = pygame.key.get_pressed()
        directions = {
            pygame.K_UP:    (-1, 0),
            pygame.K_DOWN:  (1, 0),
            pygame.K_LEFT:  (0, -1),
            pygame.K_RIGHT: (0, 1),
        }
        for key, (dr, dc) in directions.items():
            if keys[key]:
                nr, nc = player_r + dr, player_c + dc
                if 0 <= nr < ROWS and 0 <= nc < COLS and grid[nr][nc] != BLOCKED:
                    player_r, player_c = nr, nc
                break

    pygame.quit()

if __name__ == "__main__":
    main()
