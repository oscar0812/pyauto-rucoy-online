#
# Simple generic rectangle that works with negative and positive
# float numbers
#
#    * A rectangle is made out of four points.
#    * Iterating over a rectangle iterates over its corner points.
#    * Screen coordinates are used (x grows from left to right, y
#      grows from top to bottom). You can still use negative numbers.
#
import random
from enum import Enum
from math import sqrt, acos, pi

from ahk import AHK
from ahk.window import Window

ahk = AHK(executable_path='C:\\Program Files\\AutoHotkey\\AutoHotKey.exe')


class Direction(Enum):
    UP = 0
    DOWN = 1
    RIGHT = 2
    LEFT = 3


class Point:
    x = None
    y = None

    def __init__(self, x, y):
        self.x, self.y = int(x), int(y)

    def __str__(self):
        return "%6.1f, %6.1f" % (self.x, self.y)

    def __eq__(self, obj):
        return obj.x == self.x and obj.y == self.y

    def distance_to_point(self, p):
        return sqrt((self.x - p.x) ** 2 + (self.y - p.y) ** 2)

    def faces_line(self, line):
        return point_faces_edge(line, self)

    def move(self, direction: Direction, num_pixels):
        if direction == Direction.UP:
            self.y -= num_pixels
        elif direction == Direction.DOWN:
            self.y += num_pixels
        elif direction == Direction.RIGHT:
            self.x += num_pixels
        elif direction == Direction.LEFT:
            self.x -= num_pixels

    def click(self):
        ahk.mouse_move(self.x, self.y)
        ahk.click(self.x, self.y)

    def move_mouse(self):
        ahk.mouse_move(self.x, self.y)


class Rectangle:
    # Screen coordinates
    l_top = None
    r_top = None
    l_bot = None
    r_bot = None
    center = None
    width = None
    height = None

    def __init__(self, x, y, width, height):
        self.__set_values__(x, y, width, height)
        self.neighbor_rectangles = []

    def __set_values__(self, x, y, width, height):
        assert width > 0
        assert height > 0
        self.l_top = Point(x, y)
        self.r_top = Point(x + width, y)
        self.r_bot = Point(x + width, y + height)
        self.l_bot = Point(x, y + height)
        self.center = Point(x + (width / float(2)), y + (height / float(2)))
        self.width = width
        self.height = height

    def __str__(self):
        str_ = ("(%4d,%4d)              (%4d,%4d)\n"
                "      .-----------------------.\n"
                "      |                       |\n"
                "      |                %6.1f |\n"
                "      |       %6.1f          |\n"
                "      '-----------------------'\n"
                "(%4d,%4d)              (%4d,%4d)"
                )
        nums = (self.l_top.x, self.l_top.y, self.r_top.x, self.r_top.y,
                self.height,
                self.width,
                self.l_bot.x, self.l_bot.y, self.r_bot.x, self.l_bot.y)
        return str_ % nums

    def __iter__(self):
        yield self.l_top
        yield self.r_top
        yield self.r_bot
        yield self.l_bot

    def iter_edges(self):
        yield self.l_top, self.r_top
        yield self.r_top, self.r_bot
        yield self.r_bot, self.l_bot
        yield self.l_bot, self.l_top

    # Gives back a copy of this rectangle
    def copy(self):
        return Rectangle(self.l_top.x, self.l_top.y, self.width, self.height)

    # Check to see if two corner points belong to the same edge
    def corners_belong_to_edge(self, c1, c2):
        return True in [
            (c1 == self.l_top and c2 == self.r_top) or
            (c1 == self.r_top and c2 == self.l_top) or
            (c1 == self.r_top and c2 == self.r_bot) or
            (c1 == self.r_bot and c2 == self.r_top) or
            (c1 == self.r_bot and c2 == self.l_bot) or
            (c1 == self.l_bot and c2 == self.r_bot) or
            (c1 == self.l_bot and c2 == self.l_top) or
            (c1 == self.l_top and c2 == self.l_bot)]

    # ______
    # |    . |
    # |______|
    def contains_point(self, point):
        return (self.l_top.x <= point.x <= self.r_top.x and
                self.l_top.y <= point.y <= self.l_bot.y)

    def random_point(self):
        return Point(random.randint(self.l_top.x, self.r_top.x), random.randint(self.l_top.y, self.r_bot.y))

    #  ______
    # |     _|____
    # |____|      |
    #      |______|
    def overlaps_with(self, rect):
        for corner in rect:
            if self.contains_point(corner):
                return True
        for corner in self:
            if rect.contains_point(corner):
                return True
        return False

    #  ______                ____ ______
    # |     _|____          |    |      |
    # |____|      |   -->   |____|______|
    #      |______|
    def align_with_top_edge_of(self, rect):
        self.l_top.y = self.r_top.y = rect.r_top.y
        self.l_bot.y = self.r_bot.y = self.l_top.y + self.height
        return self

    #  ______                ______
    # |     _|____          |______|
    # |____|      |   -->   |      |
    #      |______|         |______|
    def align_with_left_edge_of(self, rect):
        self.l_top.x = self.l_bot.x = rect.l_top.x
        self.r_top.x = self.r_bot.x = self.l_top.x + self.width
        return self

    # ______
    # |      |
    # |______|
    #    ______
    #   |      |
    #   |______|
    def overlaps_on_x_axis_with(self, rect):
        return self.copy().align_with_top_edge_of(rect).overlaps_with(rect)

    # ______
    # |      |   ______
    # |______|  |      |
    #          |______|
    def overlaps_on_y_axis_with(self, rect):
        return self.copy().align_with_left_edge_of(rect).overlaps_with(rect)

    # ______
    # |      |             The calculation includes
    # |______|             both edges and corners.
    #        \ d
    #         \ ______
    #          |      |
    #          |______|
    def distance_to_rectangle(self, rect):

        # 1. see if they overlap
        if self.overlaps_with(rect):
            return 0

        # 2. draw a line between rectangles
        line = (self.center, rect.center)

        # 3. find the two edges that intersect the line
        edge1 = None
        edge2 = None
        for edge in self.iter_edges():
            if lines_intersect(edge, line):
                edge1 = edge
                break
        for edge in rect.iter_edges():
            if lines_intersect(edge, line):
                edge2 = edge
                break
        assert edge1
        assert edge2

        # 4. find the shortest distance between these two edges
        distances = [
            distance_between_edge_and_point(edge1, edge2[0]),
            distance_between_edge_and_point(edge1, edge2[1]),
            distance_between_edge_and_point(edge2, edge1[0]),
            distance_between_edge_and_point(edge2, edge1[1]),
        ]

        return min(distances)

    def shift_rectangle_down(self, number_of_pixels):
        return Rectangle(self.l_top.x, self.l_top.y + number_of_pixels, self.width, self.height)

    def move_mouse_around(self):
        speed_ = 20
        ahk.mouse_move(self.l_top.x, self.l_top.y, speed=speed_)
        ahk.mouse_move(self.r_top.x, self.r_top.y, speed=speed_)
        ahk.mouse_move(self.r_bot.x, self.r_bot.y, speed=speed_)
        ahk.mouse_move(self.l_bot.x, self.l_bot.y, speed=speed_)

    def move_mouse_to_center(self):
        speed_ = 20
        ahk.mouse_move(self.center.x, self.center.y, speed=speed_)


def create_rectangle_from_ahk_window(ahk_window: Window):
    p = ahk_window.get_pos()
    return Rectangle(p[0], p[1], p[2], p[3])


# ---------------------- Math primitive functions ----------------------


def distance_between_points(point1, point2):
    return point1.distance_to_point(point2)


def distance_between_rectangles(rect1, rect2):
    return rect1.distance_to_rectangle(rect2)


def triangle_area_at_points(p1, p2, p3):
    a = p1.distance_to_point(p2)
    b = p2.distance_to_point(p3)
    c = p1.distance_to_point(p3)
    s = (a + b + c) / float(2)
    area = sqrt(s * (s - a) * (s - b) * (s - c))
    return area


# Finds angle using cos law
def angle(a, b, c):
    divid = (a ** 2 + b ** 2 - c ** 2)
    divis = (2 * a * b)
    if divis > 0:
        result = float(divid) / divis
        if 1.0 >= result >= -1.0:
            return acos(result)
        return 0
    else:
        return 0


# Checks if point faces edge
def point_faces_edge(edge, point):
    a = edge[0].distance_to_point(edge[1])
    b = edge[0].distance_to_point(point)
    c = edge[1].distance_to_point(point)
    ang1, ang2 = angle(b, a, c), angle(c, a, b)
    if ang1 > pi / 2 or ang2 > pi / 2:
        return False
    return True


def lines_intersect(line1, line2):
    return lines_overlap_on_x_axis(line1, line2) and lines_overlap_on_y_axis(line1, line2)


def lines_overlap_on_x_axis(line1, line2):
    x1, x2, = line1[0].x, line1[1].x
    x3, x4, = line2[0].x, line2[1].x
    e1_left, e1_right = min(x1, x2), max(x1, x2)
    e2_left, e2_right = min(x3, x4), max(x3, x4)
    return (e2_left <= e1_left <= e2_right) or (e2_left <= e1_right <= e2_right) or \
           (e1_left <= e2_left <= e1_right) or (e1_left <= e2_right <= e1_right)


def lines_overlap_on_y_axis(line1, line2):
    y1, y2, = line1[0].y, line1[1].y
    y3, y4, = line2[0].y, line2[1].y
    e1_top, e1_bot = min(y1, y2), max(y1, y2)
    e2_top, e2_bot = min(y3, y4), max(y3, y4)
    return (e2_top <= e1_top <= e2_bot) or (e2_top <= e1_bot <= e2_bot) or \
           (e1_top <= e2_top <= e1_bot) or (e1_top <= e2_bot <= e1_bot)


# Gives distance if the point is facing edge, else False
def distance_between_edge_and_point(edge, point):  # edge is a tuple of points
    if point_faces_edge(edge, point):
        area = triangle_area_at_points(edge[0], edge[1], point)
        base = edge[0].distance_to_point(edge[1])
        height = area / (0.5 * base)
        return height
    return min(distance_between_points(edge[0], point),
               distance_between_points(edge[1], point))


# get the midpoint between p1 and p2
def midpoint(p1, p2):
    return Point((p1.x + p2.x) / 2, (p1.y + p2.y) / 2)


# get the rectangle center points and calculate based on that
def closest_rectangle_from_point(point: Point, rectangles):
    closest_rectangle = None
    if len(rectangles) > 0:
        # sort rectangles based on point
        rectangles.sort(key=lambda r: (r.center.x - point.x) ** 2 +
                                      (r.center.y - point.y) ** 2)
        closest_rectangle = rectangles[0]

    return closest_rectangle
