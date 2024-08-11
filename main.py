import pyxel

WIDTH, HEIGHT = 128, 128
# 描画時に透明色として扱う色を指定する（この色は描画されない）
TRANSPARENT_COLOR = 12
SCENE_TITLE = 0
SCENE_GAME = 1
SCENE_RESULT = 2
# 結局使わなかった
# BOY_STATUS_LIVE = 0
# BOY_STATUS_DEAD = 1
# boyに最大どれだけ遅れてカメラが追従するか
SCROLL_BORDER_X = 80
GRAVITY = 0.1
CHECK_POINTS = [
    [-1, -1],
    [16, -1],
    [16, 16],
    [-1, 16],
    [8, -1],
    [16, 8],
    [8, 16],
    [-1, 8],
]
JUMP_VELOCITY = -3


def get_tile(x, y):
    return pyxel.tilemap(0).pget(x, y)


def detect_collision(x, y):
    coll_flags = []
    for [px, py] in CHECK_POINTS:
        # アルファベット順に確認していく
        if (
            get_tile((x + px) // 8, (y + py) // 8)[1] == 6
            or get_tile((x + px) // 8, (y + py) // 8)[1] == 7
        ):
            coll_flags.append(True)
        else:
            coll_flags.append(False)
    return coll_flags


class Boy:
    def __init__(self, x, y, w=16, h=16):
        self.x, self.y, self.w, self.h = x, y, w, h
        self.v_y, self.status_alive = 0, True
        self.prev_x, self.prev_y = x, y
        # １の時はjump中
        self.jump_status = 1

    def update(self, scroll_x, enemies, game_scene):
        """フレームごとに状態を更新するメソッド"""
        # 一つ前の座標（更新前の座標）を保持しておく
        self.prev_x = self.x
        self.prev_y = self.y
        # self.check_enemy_collision(enemy)
        coll_flags = detect_collision(self.x, self.y)

        if pyxel.btn(pyxel.KEY_LEFT) and self.x > scroll_x and not (coll_flags[7]):
            self.x -= 2
        if (
            pyxel.btn(pyxel.KEY_RIGHT)
            and self.x < scroll_x + WIDTH - self.w
            and not (coll_flags[5])
        ):
            self.x += 2
        if self.x > scroll_x + SCROLL_BORDER_X:
            scroll_x = min(self.x - SCROLL_BORDER_X, 240 * 8)

        self.v_y += GRAVITY
        if self.v_y < 0:
            jumping_distance = 0
            while jumping_distance >= self.v_y:
                jumping_coll_flags = detect_collision(self.x, self.y + jumping_distance)
                if (
                    jumping_coll_flags[0]
                    or jumping_coll_flags[1]
                    or jumping_coll_flags[4]
                ):
                    self.v_y = 0
                    self.y += jumping_distance
                    break
                jumping_distance -= 1
        else:
            falling_distance = 0
            # while falling_distance <= self.v_y:
            #     # 下から順に衝突判定をしていく
            #     falling_coll_flags = detect_collision(self.x, self.y + falling_distance)
            #     if falling_coll_flags[2] or falling_coll_flags[3] or falling_coll_flags[6]:
            #         self.v_y = 0
            #         # 衝突した位置まで座標を移動（上に移動）
            #         self.y += falling_distance
            #         break
            #     falling_distance += 1
            while falling_distance <= self.v_y:
                falling_coll_flags = detect_collision(self.x, self.y + falling_distance)
                if falling_coll_flags[2] or falling_coll_flags[3]:
                    # ブロックの単位が8なので
                    self.y = ((self.y + falling_distance) // 8) * 8
                    self.v_y = 0
                    self.jump_status = 0
                    break
                falling_distance += 8
        self.y += self.v_y

        if coll_flags[2] or coll_flags[3] or coll_flags[6]:
            pass
        else:
            self.y += self.v_y
        # 地面についている時だけjump可能にする
        if pyxel.btnp(pyxel.KEY_SPACE) and (coll_flags[2] or coll_flags[3]):
            self.v_y = JUMP_VELOCITY
            self.jump_status = 1

        # 落下時のアウト判定
        if self.y > 128:
            game_scene = SCENE_RESULT
            self.status_alive = False
            pyxel.play(0, 2, loop=True)
            pyxel.play(1, 4)
        # 衝突判定は座標の更新が終わってから実行する
        enemies, game_scene = self.check_enemy_collision(enemies, game_scene)

        return scroll_x, enemies, game_scene

    def check_enemy_collision(self, enemies, game_scene):
        """Enemyの情報をもとに衝突判定を行う"""
        for enemy in enemies:
            if (
                self.x < enemy.x + enemy.w
                and self.x > enemy.x - self.w
                and self.y < enemy.y + enemy.h
                and self.y > enemy.y - self.h
            ):
                # 重なりがあり、かつ...
                if (
                    # 一つ前の状態でenemyの幅の中にいる
                    self.prev_x < enemy.x + enemy.w
                    and self.prev_x > enemy.x - self.w
                    # かつ上側にいる
                    and self.prev_y < enemy.y - self.h
                ):
                    print("beat")
                    enemies.remove(enemy)
                    pyxel.play(1, 3)
                else:
                    # print("game over")
                    self.status_alive = False
                    game_scene = SCENE_RESULT
                    pyxel.play(0, 2, loop=True)
                    pyxel.play(1, 4)
        return enemies, game_scene

    def draw(self):
        """舞フレームごとに描画するメソッド"""
        # frame_count(ゲームが開始されてからのフレーム数をカウントする　１秒間あたり30回更新)
        # if self.jump_status:
        #     u = 3 * 16
        # else:
        #     u = pyxel.frame_count // 3 % 2 * 16
        u = 3 * 16 if self.jump_status else pyxel.frame_count // 3 % 2 * 16
        # blt(組み込みの描画メソッド)
        pyxel.blt(self.x, self.y, 0, u, 16, self.w, self.h, TRANSPARENT_COLOR)


class Enemy:
    def __init__(self, x, y, w=16, h=16, v_x=0.5):
        self.x, self.y, self.w, self.h, self.v_x, self.v_y = x, y, w, h, v_x, 0

    def update(self):
        # self.x -= self.v_x
        self.v_y += GRAVITY
        falling_distance = 0
        while falling_distance <= self.v_y:
            coll_flags = detect_collision(self.x, self.y + falling_distance)
            if coll_flags[2] or coll_flags[3] or coll_flags[6]:
                self.v_y = 0
                self.y += falling_distance
                break
            falling_distance += 1
        self.y += self.v_y

    def draw(self):
        u = pyxel.frame_count // 6 % 2 * 16
        pyxel.blt(self.x, self.y, 0, u, 88, self.w, self.h, TRANSPARENT_COLOR)


class App:
    def __init__(self):
        pyxel.init(WIDTH, HEIGHT)
        pyxel.load("./scene.pyxres")
        self.scene = SCENE_TITLE
        # BGM
        pyxel.sounds[0].set(
            "e3 e3 e3 c3 e3 g3 g2 "
            "c3 g2 e2 a2 b2 a#2 a2 g2 e3 g3 a3 f3 g3 e3 c3 d3 b2 ",
            "p",
            "6",
            "vffn fnff vffs vfnn",
            25,
        )
        pyxel.sounds[1].set(
            "c3 c4 a2 a3 a#2 a3 g2 e3 g3 a3 f3 g3 e3 c3 d3 b2 "
            "c3 g2 e2 a2 b2 a#2 a2 g2 e3 g3 a3 f3 g3 e3 c3 d3 b2 ",
            "s",
            "6",
            "nnff vfff vvvv vfff svff vfff vvvv svnn",
            25,
        )
        pyxel.sounds[2].set(
            "f0ra4r f0ra4r f0ra4r f0f0a4r", "n", "6622 6622 6622 6422", "f", 25
        )
        # コイン獲得時の効果音
        pyxel.sounds[3].set("c3e3g3e4g4", "t", "6", "f", 5)
        # ゲームオーバー時の効果音
        pyxel.sounds[4].set("g2f2e2d2c2", "t", "76543", "fffnn", 10)
        # 成功時の効果音
        pyxel.sounds[5].set("c3e3g3c4e4", "p", "66443", "nnffn", 10)
        # 失敗時の効果音
        pyxel.sounds[6].set("g2f2e2d2c2", "t", "76543", "fffnn", 10)

        pyxel.play(0, 2, loop=True)
        self.game_settings()

    def check_goal(self):
        # 座標を用いて判定する
        # if self.boy.x>1176:
        #     return True
        # else:
        #     return False
        # 旗との当たり判定を使用する
        for x, y in CHECK_POINTS:
            if get_tile((self.boy.x + x) // 8, (self.boy.y + y) // 8)[1] == 14:
                return True
            return False

    def game_settings(self):
        pyxel.image(0).rect(0, 80, 16, 8, TRANSPARENT_COLOR)
        self.boy = Boy(0, 0)
        self.scroll_x = 0
        # self.enemy = Enemy(80, 0)
        # self.enemies = [Enemy(70, 0), Enemy(100, 0)]
        self.enemies = []
        # 今後表示する敵のストック
        self.enemy_lines = [
            {
                "x": 100,
                "y": 0,
                "appear": False,
            },
            {
                "x": 200,
                "y": 96,
                "appear": False,
            },
        ]
        pyxel.run(self.update, self.draw)

    def update_title_scene(self):
        if pyxel.btnp(pyxel.KEY_SPACE):
            self.scene = SCENE_GAME
            pyxel.play(0, [0, 1], loop=True)
            self.game_settings()

    def update_game_scene(self):
        # boyがある一定のラインを超えたところでenemyを出現させる
        for enemy_line in self.enemy_lines:
            if self.boy.x > enemy_line["x"] and not enemy_line["appear"]:
                self.enemies.append(Enemy(enemy_line["x"] + 60, enemy_line["y"]))
                enemy_line["appear"] = True
        # スクロールの更新
        # self.scroll_x = self.boy.update(self.scroll_x, self.enemy)
        self.scroll_x, self.enemies, self.scene = self.boy.update(
            self.scroll_x, self.enemies, self.scene
        )
        # self.enemy.update()
        for enemy in self.enemies:
            enemy.update()
        if self.check_goal():
            # print("goal")
            self.scene = SCENE_RESULT
            pyxel.play(0, 2, loop=True)
            pyxel.play(1, 5)

    def update_result(self):
        if pyxel.btnp(pyxel.KEY_SPACE):
            self.scene = SCENE_GAME
            pyxel.play(0, [0, 1], loop=True)
            self.game_settings()
        elif pyxel.btnp(pyxel.KEY_R):
            self.scene = SCENE_TITLE

    def update(self):
        if self.scene == SCENE_TITLE:
            self.update_title_scene()
        elif self.scene == SCENE_GAME:
            self.update_game_scene()
        elif self.scene == SCENE_RESULT:
            self.update_result()

    def draw_title_scene(self):
        pyxel.text(self.scroll_x + 36, 40, "SUPER MAN DASH", 7)
        pyxel.text(self.scroll_x + 28, 80, "-STAER[ SPACE ] -", 7)

    def draw_game_scene(self):
        pyxel.camera()
        pyxel.bltm(0, 0, 0, self.scroll_x, 0, WIDTH, HEIGHT)
        pyxel.camera(self.scroll_x, 0)
        self.boy.draw()
        # self.enemy.draw()
        for enemy in self.enemies:
            enemy.draw()

    def draw_result(self):
        # ==Trueはリンターが怒るので消した
        if self.boy.status_alive:
            pyxel.text(self.scroll_x + 36, 40, "YOU SUCCESSED", 7)
        else:
            pyxel.text(self.scroll_x + 36, 40, "YOU FAILED", 7)
        pyxel.text(self.scroll_x + 28, 60, "- RESTART [ R ] -", 7)
        pyxel.text(self.scroll_x + 28, 80, "- RETURN [ SPACE ] -", 7)

    def draw(self):
        # 画面をクリアする
        pyxel.cls(0)
        if self.scene == SCENE_TITLE:
            self.draw_title_scene()
        elif self.scene == SCENE_GAME:
            self.draw_game_scene()
        elif self.scene == SCENE_RESULT:
            self.draw_result()


App()
