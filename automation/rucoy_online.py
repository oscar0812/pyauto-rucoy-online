import random
import time
from collections import Counter

from colormap import rgb2hex

from images import ScreenImage, image_to_cv
from geometry import Rectangle, Point, closest_rectangle_from_point


class MobDen:

    def __init__(self, tile_colors, mob_img_urls):
        self.tile_colors = tile_colors
        self.cv_img_templates = [image_to_cv(img) for img in mob_img_urls]


class RucoyOnline:

    MOB_DENS = {'vampire': MobDen(tile_colors=['#584836'], mob_img_urls=['imgs/rucoy_online/vampire_white.png']),
                'skeleton_ground_level': MobDen(tile_colors=['#1C4548', '#29382C'],
                                                mob_img_urls=['imgs/rucoy_online/skeleton_warrior_white.png'])}

    current_mob_den = MOB_DENS['vampire']

    arrow_number_cvs = {i: image_to_cv(f'imgs/rucoy_online/arrow_amount_numbers/{i}.png') for i in range(0, 10)}
    exhausted_mob_message = image_to_cv('imgs/rucoy_online/exhausted_mob.png')
    skeleton_stairs = image_to_cv('imgs/rucoy_online/skeleton_stairs_down.png')

    def __init__(self, window_rec: Rectangle):
        self.window_rec = window_rec
        self.right_navbar_margin, self.top_navbar_margin = 35, 35

        # calculate all rectangle, from clickable buttons to others
        self.__calculate_tile_rectangles__()
        self.__calculate_left_bottom_rectangles()
        self.__calculate_top_right_rectangles()
        self.__calculate_player_rectangle()

    # calculate rectangles for special ability, mana, and health
    def __calculate_left_bottom_rectangles(self):
        l_bot = self.window_rec.l_bot
        b_width, b_height = 65, 80
        # special is first, then mana, then health. work from top to bottom
        self.special_ability_rectangle = Rectangle(l_bot.x + 8, l_bot.y - (3 * b_height), b_width, b_height - 10)
        self.mana_potion_rectangle = Rectangle(l_bot.x + 8, l_bot.y - (2 * b_height), b_width, b_height - 10)
        self.health_potion_rectangle = Rectangle(l_bot.x + 8, l_bot.y - b_height, b_width, b_height - 10)

    # calculate rectangles for menus items on top right (including back button)
    def __calculate_top_right_rectangles(self):
        r_top = self.window_rec.r_top
        b_width, b_height = 50, 50

        self.map_rectangle = Rectangle(r_top.x - (4 * b_width) - self.right_navbar_margin - 12,
                                       r_top.y + self.top_navbar_margin, b_width, b_height)

        self.chat_rectangle = Rectangle(r_top.x - (3 * b_width) - self.right_navbar_margin - 8,
                                        r_top.y + self.top_navbar_margin, b_width, b_height)

        self.friends_rectangle = Rectangle(r_top.x - (2 * b_width) - self.right_navbar_margin - 4,
                                           r_top.y + self.top_navbar_margin, b_width, b_height)

        self.settings_rectangle = Rectangle(r_top.x - b_width - self.right_navbar_margin,
                                            r_top.y + self.top_navbar_margin, b_width, b_height)

        self.back_rectangle = self.settings_rectangle.copy()

        # this pixel will be white if the back button is there
        self.back_button_point = Point(r_top.x - self.right_navbar_margin - 40, r_top.y + self.top_navbar_margin + 20)
        # self.back_button_point.move_mouse()

    # box around the player, so we don't accidentally touch em
    def __calculate_player_rectangle(self):
        p_tile = closest_rectangle_from_point(self.window_rec.center, self.tile_rectangles)
        margin = 10
        self.player_rectangle = Rectangle(p_tile.l_top.x - margin, p_tile.l_top.y - margin,
                                          p_tile.width + (2 * margin), p_tile.height + (2 * margin))

    def __calculate_tile_rectangles__(self):
        x_current, y_current = 84, 89
        x_spacing, y_spacing = 5.1, 5.09  # this is the best spacing I could find that finds all rectangles perfectly

        num_cols, num_rows = 13, 7

        self.tile_width, self.tile_height = 49, 49

        rectangles = []
        for col in range(0, num_cols):
            space_to_next_x = (col * self.tile_width + col * x_spacing)
            row_rec = Rectangle(x_current + space_to_next_x, y_current, self.tile_width, self.tile_height)
            rectangles.append(row_rec)
            for row in range(1, num_rows):
                # the rest of the rows
                rectangles.append(row_rec.shift_rectangle_down(self.tile_height * row + y_spacing * row))

        # calculate neighbors
        for index_, rec in enumerate(rectangles):
            col = int(index_ / num_rows)
            row = index_ % num_rows
            # top
            if row > 0:
                rec.neighbor_rectangles.append(rectangles[index_ - 1])

            # bottom
            if row < num_rows - 1:
                rec.neighbor_rectangles.append(rectangles[index_ + 1])

            # left
            if col > 0:
                rec.neighbor_rectangles.append(rectangles[index_ - num_rows])

            # right
            if col < num_cols - 1:
                rec.neighbor_rectangles.append(rectangles[index_ + num_rows])

        self.tile_rectangles = rectangles

        x1, y1 = rectangles[0].l_top.x, rectangles[0].l_top.y
        x2, y2 = rectangles[-1].r_bot.x, rectangles[-1].r_bot.y
        self.clickable_area_rectangle = Rectangle(x1, y1, x2 - x1, y2 - y1)

    def __update_screenshot__(self):
        self.current_screen_image = ScreenImage(self.window_rec)

    def print_center_colors(self):
        hex_strings = [self.get_hex_color_at_point(tr.center) for tr in self.tile_rectangles]
        counts = Counter(hex_strings)
        print(counts)

    def mob_is_exhausted(self):
        rec = self.current_screen_image.find_on_screen(self.exhausted_mob_message)
        return len(rec) > 0

    def get_mob_rectangles(self):
        # get all mobs
        name_recs = self.current_screen_image.find_on_screen(self.current_mob_den.cv_img_templates[0])
        # try to land a point in the mob by moving the point down and to the right
        # we have to push 3/4 of a tile down since the name is on top of the tile (sometimes way up)
        point_touching_mobs = [Point(nr.center.x, nr.center.y + (self.tile_height * (3 / 4))) for nr in name_recs]

        # name_recs start at the beginning of the name, so move the box down and to the right
        mob_rectangles = [closest_rectangle_from_point(p, self.tile_rectangles) for p in point_touching_mobs]

        # get the center of monster mob_rectangles and sort by closest to player
        mob_rectangles.sort(key=lambda r: (r.center.x - self.player_rectangle.center.x) ** 2 +
                                          (r.center.y - self.player_rectangle.center.y) ** 2)

        return mob_rectangles

    def get_hex_color_at_point(self, point: Point):
        rgb = self.current_screen_image.pillow_img.getpixel((point.x, point.y))
        return rgb2hex(rgb[0], rgb[1], rgb[2])

    def has_back_button(self):
        color = self.get_hex_color_at_point(self.back_button_point)
        return color == '#C9C9C9'

    def get_clickable_tiles(self, tile_list=None):
        if tile_list is None:
            tile_list = self.tile_rectangles

        return [tile for tile in tile_list if
                self.get_hex_color_at_point(tile.center) in self.current_mob_den.tile_colors]

    def can_click_point(self, p: Point):
        # we can click a point if it's in the clickable tiles but not on the player
        can_click = self.clickable_area_rectangle.contains_point(p) \
                    and not self.player_rectangle.contains_point(p)

        # don't click on stairs
        stairs_rec = self.current_screen_image.find_on_screen(self.skeleton_stairs)
        if len(stairs_rec) > 0:
            stairs_rec = closest_rectangle_from_point(stairs_rec[0].center, self.tile_rectangles)
            can_click = can_click and not stairs_rec.contains_point(p)

        return can_click

    def needs_health(self):
        # get a pixel at the end of the health bar
        x_margin, y_margin = 260, 10 + self.top_navbar_margin
        point = Point(self.window_rec.l_top.x + x_margin, self.window_rec.l_top.y + y_margin)
        # health bar is gray
        color = self.get_hex_color_at_point(point)
        return color == '#696969'

    def needs_mana(self):
        # get a pixel at the end of the mana bar
        point = Point(self.window_rec.l_top.x + 260, self.window_rec.l_top.y + self.top_navbar_margin + 28)
        # mana bar is gray
        color = self.get_hex_color_at_point(point)
        return color == '#696969'

    # read the arrow images left to right (sort by the x-axis)
    def __read_num_arrows_from_screen__(self):
        x_dictionary = {}
        for i, num_cv in self.arrow_number_cvs.items():
            for rec in self.current_screen_image.find_on_screen(num_cv, threshold=0.9):
                x_dictionary[rec.l_top.x] = str(i)

        if len(x_dictionary.keys()) > 0:
            num_string = ''.join([x_dictionary[key] for key in sorted(x_dictionary.keys())])
        else:
            num_string = '0'
        return int(num_string)

    def click_back_button_out_of_existence(self):
        while self.has_back_button():
            self.back_rectangle.random_point().click()
            time.sleep(random.uniform(0.2, 0.5))
            self.__update_screenshot__()

    # need to check multiple times as sometimes the chat blocks the numbers
    def get_num_arrows(self):
        current_num_arrows = 0

        for i in range(0, 120):
            current_num_arrows = self.__read_num_arrows_from_screen__()
            if current_num_arrows > 0:
                break
            else:
                print(f'0 arrows at loop #{i}')
                time.sleep(random.uniform(1, 2))
            self.__update_screenshot__()

        return current_num_arrows

    def trigger_special_ability(self, times=1):
        for i in range(0, times):
            time.sleep(random.uniform(1, 3))
            # trigger special ability
            self.special_ability_rectangle.random_point().click()
            if self.needs_mana():

                self.mana_potion_rectangle.random_point().click()

    def automate_training(self):
        while 1:
            min_timeout, max_timeout = 6, 8
            self.__update_screenshot__()

            self.click_back_button_out_of_existence()

            if self.get_num_arrows() == 0:
                # no arrows
                break

            if self.needs_health():
                self.health_potion_rectangle.random_point().click()
                self.trigger_special_ability(times=1)

            # mob is exhausted, trigger special
            if self.mob_is_exhausted():
                self.trigger_special_ability(times=2)

            # click on the mob and any neighbor rectangles
            mob_rectangles = self.get_mob_rectangles()

            if len(mob_rectangles) > 0:
                clickable_points = []
                point = mob_rectangles[0].random_point()
                clickable_points.append(point)

                neighbor_tiles = self.get_clickable_tiles(mob_rectangles[0].neighbor_rectangles)
                if len(neighbor_tiles) > 0:
                    neighbor_tile = random.choice(neighbor_tiles)
                    clickable_points.append(neighbor_tile.random_point())

                for p in clickable_points:
                    if self.can_click_point(p):
                        p.click()

            else:
                # no monsters
                clickable_tiles = self.get_clickable_tiles()
                if len(clickable_tiles) > 0:
                    random_point = random.choice(clickable_tiles).random_point()

                    if self.can_click_point(random_point):
                        random_point.click()
                min_timeout, max_timeout = 1, 2

            time.sleep(random.uniform(min_timeout, max_timeout))
