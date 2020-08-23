import tkinter as tk
import random

FILENAME_WORLD = 'world'

MARGIN_X, MARGIN_Y = 15, 15
CELL_WIDTH, CELL_HEIGHT = 25, 25
STATUS_WIDTH, STATUS_HEIGHT = 20, 10

LENGTH_PLAN = 50
NUM_PLANS = 5000
NUM_SELECTS = 100
PROB_MUTATE = 0.03

MAP_COLOR = {
    'road' : 'skyblue',
    'start' : 'red',
    'end' : 'blue',
    'wall' : 'white',
    'player' : 'brown'
}

MAP_MOVE = {
    0 : (0, -1),
    90 : (1, 0),
    180 : (0, 1),
    270 : (-1, 0)
}

MAP_SCORE = {
    'road' : 20,
    'start' : 0,
    'end' : 500,
    'wall' : 1
}

# -----------------------------------------------------------

def read_world():
    with open(FILENAME_WORLD, 'r') as p:
        lines = [_f for _f in map(str.strip, p.readlines()) if _f]

    convert = {'.' : 'wall', 'r' : 'road', 's' : 'start', 'e' : 'end'}
    
    w, h = len(lines[0]), len(lines)
    world = [[convert[lines[i][j]] for j in range(w)]
             for i in range(h)]
    
    return world

def pad_string(sentence, length):
    length_front = int((length - len(sentence))/2)
    length_back = length - length_front - len(sentence)

    return ' '*length_front + sentence + ' '*length_back

def generate_binaries(length, num_samples):
    samples = []

    for i in range(length):
        num = random.randint(0, (2**length)-1)
        samples.append(list(map(int, bin(num)[2:].zfill(length))))

    return samples

# -----------------------------------------------------------

class MainApp(tk.Frame, object):
    def __init__(self, parent = None):
        self.parent = parent
        super(MainApp, self).__init__(self.parent)

        self.parent.protocol('WM_DELETE_WINDOW', self.quit)

        # read the data
        self.world = read_world()

        # initialize
        self.plans = []

        # set UI
        self.init_frames()
        self.init_world()
        self.init_player()
        self.init_buttons()
        self.init_status()

    # --------------------------------------------------------
    # UI initialization

    def init_frames(self):
        self.frame_board = tk.Frame(self)
        self.frame_control = tk.Frame(self)
        self.frame_board.grid(row = 0, column = 0)
        self.frame_control.grid(row = 0, column = 1, padx = 10)

        self.frame_buttons = tk.Frame(self.frame_control)
        self.frame_status = tk.Frame(self.frame_control)
        self.frame_buttons.grid(row = 0, column = 0, pady = 10)
        self.frame_status.grid(row = 1, column = 0, pady = 10)

    def init_world(self):
        self.dim_x, self.dim_y = len(self.world[0]), len(self.world)
        self.width = self.dim_x * CELL_WIDTH + MARGIN_X * 2
        self.height = self.dim_y * CELL_HEIGHT + MARGIN_Y * 2

        self.board = tk.Canvas(
            self.frame_board, bg = 'white',
            width = self.width, height = self.height
        )
        self.board.pack()

        self.id_world = [[self.board.create_rectangle(
            MARGIN_X + CELL_WIDTH * j,
            MARGIN_Y + CELL_HEIGHT * i,
            MARGIN_X + CELL_WIDTH * (j+1),
            MARGIN_Y + CELL_HEIGHT * (i+1),
            fill = MAP_COLOR[self.world[i][j]],
            tags = 'world')
            for j in range(self.dim_x)]
            for i in range(self.dim_y)]

    def init_player(self):
        for i in range(self.dim_y):
            for j in range(self.dim_x):
                if self.world[i][j] == 'start':
                    self.start_i, self.start_j = i, j
                    break

        self.player_i, self.player_j = self.start_i, self.start_j
        self.player_angle = 0 # 0 = up / 180 = down

        self.id_player = self.board.create_polygon(
            MARGIN_X + CELL_WIDTH*self.player_j + CELL_WIDTH/2,
            MARGIN_Y + CELL_HEIGHT*self.player_i + CELL_HEIGHT/8,
            MARGIN_X + CELL_WIDTH*self.player_j + CELL_WIDTH/5,
            MARGIN_Y + CELL_HEIGHT*self.player_i + (CELL_HEIGHT*7)/8,
            MARGIN_X + CELL_WIDTH*self.player_j + (CELL_WIDTH*4)/5,
            MARGIN_Y + CELL_HEIGHT*self.player_i + (CELL_HEIGHT*7)/8,
            fill = MAP_COLOR['player'],
            tags = 'player')

    def init_buttons(self):
        self.button_new = tk.Button(
            self.frame_buttons,
            text = pad_string('new', 15),
            command = self.callback_new
        )

        self.button_evolve = tk.Button(
            self.frame_buttons,
            text = pad_string('evolve', 15),
            command = self.callback_evolve
        )

        self.button_clear = tk.Button(
            self.frame_buttons,
            text = pad_string('clear', 15),
            command = self.callback_clear
        )

        self.button_new.pack(pady = 3)
        self.button_evolve.pack(pady = 3)
        self.button_clear.pack(pady = 3)

    def init_status(self):
        self.text_status = tk.Text(
            self.frame_status,
            width = STATUS_WIDTH,
            height = STATUS_HEIGHT
        )

        self.scroll_status = tk.Scrollbar(
            self.frame_status,
            command = self.text_status.yview
        )

        self.text_status.grid(row = 0, column = 0, sticky = 'nsew')
        self.scroll_status.grid(row = 0, column = 1, sticky = 'nsew')

        self.text_status['yscrollcommand'] = self.scroll_status.set

    # --------------------------------------------------------
    # callbacks for buttons

    def callback_new(self):
        self.plans = generate_binaries(LENGTH_PLAN, NUM_PLANS)
        self.write_status('Generated %d samples of length %d.\n'\
                          % (NUM_PLANS, len(self.plans[0])))

    def callback_evolve(self):
        if not self.plans:
            return

        selects = self.select_plans(self.plans, NUM_SELECTS)
        self.write_status('Selected %d plans from the parents.\n'\
                          % NUM_SELECTS)

        childs = []

        for i in range(NUM_PLANS):
            parent_1 = random.choice(selects)
            parent_2 = random.choice(selects)
            childs.append(self.crossover_plans(parent_1, parent_2))
        
        self.write_status('%d childs are born.\n' % NUM_PLANS)

        self.plans = list(map(self.mutate_plan, childs))
        self.write_status('Some childs are mutated.\n')

        self.write_status('Evolution finished.'\
                          ' Playing the best plan...\n')

        plan_best = self.plans[0]
        score_best = self.get_score(plan_best)

        for p in self.plans:
            if self.get_score(p) > score_best:
                plan_best = p

        self.restore_player()
        self.start_trip(plan_best, 0.03)

    def callback_clear(self):
        self.clear_status()
    
    # --------------------------------------------------------
    # status panel

    def write_status(self, sentence):
        self.text_status.insert('insert', sentence)

    def clear_status(self):
        self.text_status.delete(1.0, 'end')
    
    # --------------------------------------------------------
    # player movement
    
    def restore_player(self):
        self.player_i, self.player_j = self.start_i, self.start_j
        self.player_angle = 0

        self.board.coords(
            self.id_player,
            MARGIN_X + CELL_WIDTH*self.player_j + CELL_WIDTH/2,
            MARGIN_Y + CELL_HEIGHT*self.player_i + CELL_HEIGHT/8,
            MARGIN_X + CELL_WIDTH*self.player_j + CELL_WIDTH/5,
            MARGIN_Y + CELL_HEIGHT*self.player_i + (CELL_HEIGHT*7)/8,
            MARGIN_X + CELL_WIDTH*self.player_j + (CELL_WIDTH*4)/5,
            MARGIN_Y + CELL_HEIGHT*self.player_i + (CELL_HEIGHT*7)/8,
        )
    
    def move_player(self, dx = 0, dy = 0):
        self.player_i += dy
        self.player_j += dx

        self.board.move(
            self.id_player, CELL_WIDTH * dx, CELL_HEIGHT * dy)

    def rotate_player(self, direction = 'right'):
        if direction == 'right':
            self.player_angle = (self.player_angle+90) % 360
        else:
            self.player_angle = (self.player_angle-90) % 360

        # Tkinter doesn't have built-in rotate() function...
        # So I had to write all the codes for each direction.
        if self.player_angle == 0: # up
            self.board.coords(
                self.id_player,
                MARGIN_X + CELL_WIDTH*self.player_j + CELL_WIDTH/2,
                MARGIN_Y + CELL_HEIGHT*self.player_i + CELL_HEIGHT/8,
                MARGIN_X + CELL_WIDTH*self.player_j + CELL_WIDTH/5,
                MARGIN_Y + CELL_HEIGHT*self.player_i + (CELL_HEIGHT*7)/8,
                MARGIN_X + CELL_WIDTH*self.player_j + (CELL_WIDTH*4)/5,
                MARGIN_Y + CELL_HEIGHT*self.player_i + (CELL_HEIGHT*7)/8
            )
        elif self.player_angle == 90: # right
            self.board.coords(
                self.id_player,
                MARGIN_X + CELL_WIDTH*self.player_j + (CELL_WIDTH*7)/8,
                MARGIN_Y + CELL_HEIGHT*self.player_i + CELL_HEIGHT/2,
                MARGIN_X + CELL_WIDTH*self.player_j + CELL_WIDTH/8,
                MARGIN_Y + CELL_HEIGHT*self.player_i + CELL_HEIGHT/5,
                MARGIN_X + CELL_WIDTH*self.player_j + CELL_WIDTH/8,
                MARGIN_Y + CELL_HEIGHT*self.player_i + (CELL_HEIGHT*4)/5,
            )
        elif self.player_angle == 180: # down
            self.board.coords(
                self.id_player,
                MARGIN_X + CELL_WIDTH*self.player_j + CELL_WIDTH/5,
                MARGIN_Y + CELL_HEIGHT*self.player_i + CELL_HEIGHT/8,
                MARGIN_X + CELL_WIDTH*self.player_j + (CELL_WIDTH*4)/5,
                MARGIN_Y + CELL_HEIGHT*self.player_i + CELL_HEIGHT/8,
                MARGIN_X + CELL_WIDTH*self.player_j + CELL_WIDTH/2,
                MARGIN_Y + CELL_HEIGHT*self.player_i + (CELL_HEIGHT*7)/8
            )
        else: # left
            self.board.coords(
                self.id_player,
                MARGIN_X + CELL_WIDTH*self.player_j + CELL_WIDTH/8,
                MARGIN_Y + CELL_HEIGHT*self.player_i + CELL_HEIGHT/2,
                MARGIN_X + CELL_WIDTH*self.player_j + (CELL_WIDTH*7)/8,
                MARGIN_Y + CELL_HEIGHT*self.player_i + CELL_HEIGHT/5,
                MARGIN_X + CELL_WIDTH*self.player_j + (CELL_WIDTH*7)/8,
                MARGIN_Y + CELL_HEIGHT*self.player_i + (CELL_HEIGHT*4)/5,
            )
    
    # --------------------------------------------------------
    # animation

    def callback_trip(self, plan, count, dt_milisec):
        # check whether the player hit the boundary of the board
        if (self.player_i < 0 or self.player_i >= self.dim_y
            or self.player_j < 0 or self.player_j >= self.dim_x):
            self.write_status('Player hit the boundary.\n')
            return

        # check whether the player hit the wall of the end
        cell = self.world[self.player_i][self.player_j]

        if cell == 'wall':
            self.write_status('Player hit the wall.\n')
            return
        
        if cell == 'end':
            self.write_status('Player reached the end.\n')
            return

        # check whether we read all numbers in the plan
        if count == len(plan):
            self.write_status('End of the plan.\n')
            return

        # 0 -> rotate right, 1 -> go front
        if plan[count] == 0:
            self.rotate_player(direction = 'right')
        else:
            self.move_player(*MAP_MOVE[self.player_angle])

        self.board.after(
            dt_milisec,
            self.callback_trip,
            plan, count+1, dt_milisec
        )

    def start_trip(self, plan, dt):
        self.write_status('Plan : %s\n' % ''.join(map(str, plan)))
        self.write_status('Starting the trip...\n')
        self.write_status('Score : %d\n' % self.get_score(plan))
        self.callback_trip(plan, 0, int(1000*dt))
    
    # --------------------------------------------------------
    # core of genetic algorithm
   
    def get_score(self, plan):
        score = 0
        angle = 0
        player_i, player_j = self.start_i, self.start_j

        cell_walked = [[False for j in range(self.dim_x)]
                       for i in range(self.dim_y)]

        for cmd in plan:
            if cmd == 0:
                angle = (angle+90) % 360
            else:
                dx, dy = MAP_MOVE[angle]
                player_i += dy
                player_j += dx
            
                if (player_i < 0 or player_i >= self.dim_y
                    or player_j < 0 or player_j >= self.dim_x):
                    break

                cell = self.world[player_i][player_j]
                
                if not cell_walked[player_i][player_j]:
                    score += MAP_SCORE[cell]
                    cell_walked[player_i][player_j] = True

                    if dy < 0:
                        score += 1

                if cell == 'wall' or cell == 'end':
                    break

        return score

    def select_plans(self, plans, num_samples): 
        scores = list(map(self.get_score, plans))
        score_min = min(scores)
        weights = [s + score_min for s in scores]
        samples = []

        for i in range(num_samples):
            value = random.randint(0, sum(weights))
            
            for j in range(len(weights)):
                value -= weights[j]

                if value <= 0:
                    samples.append(plans[j])
                    break

        return samples

    def crossover_plans(self, plan_1, plan_2):
        sep = random.randint(0, len(plan_1)-1)
        return plan_1[:sep] + plan_2[sep:]

    def mutate_plan(self, plan):
        plan_mutated = plan[:]

        if random.random() <= PROB_MUTATE:
            i = random.randint(0, len(plan)-1)
            plan_mutated[i] = 1 - plan_mutated[i]

        return plan_mutated
        
    # --------------------------------------------------------
    # main routine

    def run(self):
        self.start_trip(list(map(int, '110110001100011111')), 0.01)
        a = generate_binaries(20, 10)
        b = self.select_plans(a, 3)
    
    # --------------------------------------------------------
    # terminate

    def quit(self):
        self.parent.destroy()

if __name__ == '__main__':
    root = tk.Tk()
    root.wm_title('PathFinder')
    app = MainApp(root)
    app.pack()
    root.mainloop()
