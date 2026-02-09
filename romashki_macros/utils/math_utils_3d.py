"""
Модуль предоставляет классы и функции для работы с элементарной трехмерной
геометрией (точками, векторами) и матрицами поворотов.
"""

import typing
import math


### CLASSES

class Point3d():
    def __init__(self,
            x: float = 0.0,
            y: float = 0.0,
            z: float = 0.0,
            ) -> None:
        self.x: float = x
        self.y: float = y
        self.z: float = z

    def __str__(self) -> str:
        return f"{self.__class__.__name__}({self.x}, {self.y}, {self.z})"

    def __repr__(self) -> str:
        return f"<{self.__str__()} at {hex(id(self))}>"

    @staticmethod
    def from_array(arr: list[float]) -> 'Point3d':
        return Point3d(arr[0], arr[1], arr[2])

    def to_array(self) -> list[float]:
        return [self.x, self.y, self.z]

    def copy(self) -> 'Point3d':
        p = Point3d()
        p.x = self.x
        p.y = self.y
        p.z = self.z
        return p

    def transform(self, transform_matrix: 'Matrix3x3'):
        """
        `Point(3*1) = TransformMatrix(3*3) * Point(3*1)`
        """
        old_x, old_y, old_z = self.to_array()
        self.x = old_x * transform_matrix.Xx + old_y * transform_matrix.Yx + old_z * transform_matrix.Zx
        self.y = old_x * transform_matrix.Xy + old_y * transform_matrix.Yy + old_z * transform_matrix.Zy
        self.z = old_x * transform_matrix.Xz + old_y * transform_matrix.Yz + old_z * transform_matrix.Zz
        return self

    def move(self, translate_vector: 'Vector3d'):
        self.x += translate_vector.x
        self.y += translate_vector.y
        self.z += translate_vector.z
        return self



class Vector3d(Point3d):
    @staticmethod
    def from_single_point(point: Point3d) -> 'Vector3d':
        v = Vector3d()
        v.x = point.x
        v.y = point.y
        v.z = point.z
        return v

    @staticmethod
    def from_points(start: Point3d, end: Point3d) -> 'Vector3d':
        v = Vector3d()
        v.x = end.x - start.x
        v.y = end.y - start.y
        v.z = end.z - start.z
        return v

    @staticmethod
    def from_array(arr: list[float]) -> 'Vector3d':
        return Vector3d(arr[0], arr[1], arr[2])

    def copy(self) -> 'Vector3d':
        return Vector3d.from_single_point(self)

    def get_length(self) -> float:
        return math.sqrt(self.x ** 2 + self.y ** 2 + self.z ** 2)

    def multiply(self, a: float):
        self.x *= a
        self.y *= a
        self.z *= a
        return self

    def normalize(self):
        return self.multiply(1 / self.get_length())


class Matrix3x3():
    """
    Матрица 3*3.
    ```
    Xx=0  Yx=0  Zx=0
    Xy=0  Yy=0  Zy=0
    Xz=0  Yz=0  Zz=0
    ```
    Также может представлять собой тройку векторов системы координат,
    каждый из готорых расположен в столбце.
    """
    def __init__(self) -> None:
        self.Xx: float = 0.0
        self.Xy: float = 0.0
        self.Xz: float = 0.0
        self.Yx: float = 0.0
        self.Yy: float = 0.0
        self.Yz: float = 0.0
        self.Zx: float = 0.0
        self.Zy: float = 0.0
        self.Zz: float = 0.0

    @staticmethod
    def get_identity_matrix():
        """
        Возвращает единичную матрицу.
        ```
        Xx=1  Yx=0  Zx=0
        Xy=0  Yy=1  Zy=0
        Xz=0  Yz=0  Zz=1
        ```
        Такая матрица может служить как:
        - матрица поворота с нулевыми поворотами вокруг осей;
        - матрица из трёх векторов X, Y, Z глобальной системы координат.
        """
        m = Matrix3x3()
        m.Xx = 1.0
        m.Yy = 1.0
        m.Zz = 1.0
        return m

    @staticmethod
    def from_array(arr: list[list[float]]) -> 'Matrix3x3':
        m = Matrix3x3()
        m.Xx, m.Yx, m.Zx = arr[0]
        m.Xy, m.Yy, m.Zy = arr[1]
        m.Xz, m.Yz, m.Zz = arr[2]
        return m

    def to_array(self) -> list[list[float]]:
        return [
            [self.Xx, self.Yx, self.Zx],
            [self.Xy, self.Yy, self.Zy],
            [self.Xz, self.Yz, self.Zz],
        ]

    @staticmethod
    def from_vectors(vectorX: Vector3d, vectorY: Vector3d, vectorZ: Vector3d) -> 'Matrix3x3':
        m = Matrix3x3()
        m.Xx = vectorX.x
        m.Xy = vectorX.y
        m.Xz = vectorX.z
        m.Yx = vectorY.x
        m.Yy = vectorY.y
        m.Yz = vectorY.z
        m.Zx = vectorZ.x
        m.Zy = vectorZ.y
        m.Zz = vectorZ.z
        return m

    def to_vectors(self) -> tuple[Vector3d, Vector3d, Vector3d]:
        return (self.get_vector_x(), self.get_vector_y(), self.get_vector_z())

    def __str__(self) -> str:
        return f"{self.__class__.__name__}{self.to_array()}"

    def __repr__(self) -> str:
        return f"<{self.__str__()} at {hex(id(self))}>"

    def get_vector_x(self) -> Vector3d:
        return Vector3d(self.Xx, self.Xy, self.Xz)

    def get_vector_y(self) -> Vector3d:
        return Vector3d(self.Yx, self.Yy, self.Yz)

    def get_vector_z(self) -> Vector3d:
        return Vector3d(self.Zx, self.Zy, self.Zz)

    def copy(self) -> 'Matrix3x3':
        m = Matrix3x3()
        m.Xx = self.Xx
        m.Xy = self.Xy
        m.Xz = self.Xz
        m.Yx = self.Yx
        m.Yy = self.Yy
        m.Yz = self.Yz
        m.Zx = self.Zx
        m.Zy = self.Zy
        m.Zz = self.Zz
        return m


### GENERAL FUNCTIONS

def get_vector_length(v: Vector3d) -> float:
    return v.get_length()


def get_scalar_product(v1: Vector3d, v2: Vector3d) -> float:
    return v1.x * v2.x + v1.y * v2.y + v1.z * v2.z


def get_vector_product(v1: Vector3d, v2: Vector3d) -> Vector3d:
    v3 = Vector3d()
    v3.x = v1.y * v2.z - v1.z * v2.y
    v3.y = v1.z * v2.x - v1.x * v2.z
    v3.z = v1.x * v2.y - v1.y * v2.x
    return v3


def project_vector_to_plane(vector: Vector3d, plane_normal: Vector3d) -> Vector3d:
    return get_vector_product(get_vector_product(plane_normal, vector), plane_normal)


def get_angle_between_vectors(v1: Vector3d, v2: Vector3d) -> float:
    sp = get_scalar_product(v1, v2)
    l1 = v1.get_length()
    l2 = v2.get_length()
    angle = math.acos(sp / l1 / l2)
    return angle


def get_angle_between_vectors_and_axis_to_rotate(vector_moving: Vector3d, vector_stationary: Vector3d) -> tuple[Vector3d, float]:
    """
    Возвращает `tuple(axis, angle)`, где
    * `axis` - ось вращения (векторное произведение исходных векторов).
    * `angle` - угол между двумя векторами, на который нужно повернуть
        вокруг оси `axis` (против часовой стрелки, если смотреть с "конца" оси)
        вектор `vector_moving` до совмещения с вектором `vector_stationary`.
    """
    v3 = get_vector_product(vector_moving, vector_stationary)
    sp = get_scalar_product(vector_moving, vector_stationary)
    l1 = vector_moving.get_length()
    l2 = vector_stationary.get_length()
    l3 = v3.get_length()
    if l3 == 0.0:
        return (Vector3d(x = 1.0), 0.0)
    angle_sin = l3 / l1 / l2
    angle_cos = sp / l1 / l2
    angle = math.atan2(angle_sin, angle_cos)
    v3.normalize()
    return v3, angle


def multiply_matrixes(m1: Matrix3x3, m2: Matrix3x3) -> Matrix3x3:
    arr1 = m1.to_array()
    arr2 = m2.to_array()
    arr3 = Matrix3x3().to_array()
    for i in range(3):
        for j in range(3):
            arr3[i][j] = 0
            for k in range(3):
                arr3[i][j] += arr1[i][k] * arr2[k][j]
    return Matrix3x3.from_array(arr3)


def get_rotation_matrix_XYZ(angle_X: float, angle_Y: float, angle_Z: float) -> Matrix3x3:
    """
    Возвращает матрицу оператора **последовательных** поворотов вокруг осей oX, oY, oZ.

    Источник: https://ru.wikipedia.org/wiki/Матрица_поворота#Матрица_поворота_в_трёхмерном_пространстве
    """
    sinA, cosA = math.sin(angle_X), math.cos(angle_X)
    sinB, cosB = math.sin(angle_Y), math.cos(angle_Y)
    sinG, cosG = math.sin(angle_Z), math.cos(angle_Z)
    m = Matrix3x3()
    m.Xx = cosB * cosG
    m.Yx = -sinG * cosB
    m.Zx = sinB
    m.Xy = sinA * sinB * cosG + sinG * cosA
    m.Yy = -sinA * sinB * sinG + cosA * cosG
    m.Zy = -sinA * cosB
    m.Xz = sinA * sinG - sinB * cosA * cosG
    m.Yz = sinA * cosG + sinB * sinG * cosA
    m.Zz = cosA * cosB
    return m


def get_rotation_matrix_Euler(alpha: float, beta: float, gamma: float) -> Matrix3x3:
    """
    Возвращает матрицу оператора поворотов на углы Эйлера.

    Источник: https://ru.wikipedia.org/wiki/Матрица_поворота#Выражение_матрицы_поворота_через_углы_Эйлера
    """
    sinA, cosA = math.sin(alpha), math.cos(alpha)
    sinB, cosB = math.sin(beta), math.cos(beta)
    sinG, cosG = math.sin(gamma), math.cos(gamma)
    m = Matrix3x3()
    m.Xx = cosA*cosG - sinA*cosB*sinG
    m.Yx = -cosA*sinG - sinA*cosB*cosG
    m.Zx = sinA*sinB
    m.Xy = sinA*cosG + cosA*cosB*sinG
    m.Yy = -sinA*sinG + cosA*cosB*cosG
    m.Zy = -cosA*sinB
    m.Xz = sinB*sinG
    m.Yz = sinB*cosG
    m.Zz = cosB
    return m


def get_rotation_matrix_around_axis(axis_vector: Vector3d, angle: float) -> Matrix3x3:
    """
    Возвращает матрицу оператора поворота вокруг произвольной оси.

    Источник: https://ru.wikipedia.org/wiki/Матрица_поворота#Матрица_поворота_вокруг_произвольной_оси
    """
    x = axis_vector.x
    y = axis_vector.y
    z = axis_vector.z
    cos = math.cos(angle)
    sin = math.sin(angle)
    m = Matrix3x3()
    m.Xx = cos + (1 - cos) * x * x
    m.Yx = (1 - cos) * x * y - sin*z
    m.Zx = (1 - cos) * x * z + sin * y
    m.Xy = (1 - cos) * y * x + sin * z
    m.Yy = cos + (1 - cos) * y * y
    m.Zy = (1 - cos) * y * z - sin * x
    m.Xz = (1 - cos) * z * x - sin * y
    m.Yz = (1 - cos) * z * y + sin * x
    m.Zz = cos + (1 - cos) * z * z
    return m


### COMPLEX FUNCTIONS

def get_CS_transform_function(
        cs_moving: Matrix3x3,
        cs_stationary: Matrix3x3 = Matrix3x3.get_identity_matrix(),
        rotation_center_point: Point3d = Point3d(),
        ) -> tuple[Matrix3x3, Vector3d]:
    """
    Возвращает `tuple(m_rotate, v_translate)`, где
    * `m_rotate` - матрица оператора вращения,
        при применении которой к системе координат `cs_moving`
        она повернется до совмещения с целевой системой координат `cs_stationary`;
    * `v_translate` - вектор для перемещения системы
        из конечной точки после применения операции вращения (`m_rotate`)
        в исходную точку `rotation_center_point`.

    Применять так и в таком порядке:
    ```python
        m_rotate, v_translate = get_CS_transform_function(
            cs_moving,
            cs_stationary,
            rotation_center_point,
        )

        point_to_rotate: Point3d = ...
        point_to_rotate.transform(m_rotate)
        point_to_rotate.move(v_translate)
    ```
    """
    rotation_center_end_point = rotation_center_point.copy()

    x_global, y_global, z_global = cs_stationary.to_vectors()

    ### 1) вращение в плоскости X до совмещения осей Y

    y_c = cs_moving.get_vector_y()
    y_c = project_vector_to_plane(y_c, x_global)

    axis, angleX_to_rotate = get_angle_between_vectors_and_axis_to_rotate(y_c, y_global)
    mX = get_rotation_matrix_around_axis(axis, angleX_to_rotate)

    cs_moving = multiply_matrixes(mX, cs_moving)
    rotation_center_end_point = rotation_center_end_point.transform(mX)

    ### 2) вращение в плоскости Z до совмещения осей Y

    y_c = cs_moving.get_vector_y()
    y_c = project_vector_to_plane(y_c, z_global)

    axis, angleZ_to_rotate = get_angle_between_vectors_and_axis_to_rotate(y_c, y_global)
    mZ = get_rotation_matrix_around_axis(axis, angleZ_to_rotate)

    cs_moving = multiply_matrixes(mZ, cs_moving)
    rotation_center_end_point = rotation_center_end_point.transform(mZ)

    ### 3) вращение в плоскости Y до совмещения осей Z

    z_c = cs_moving.get_vector_z()
    z_c = project_vector_to_plane(z_c, y_global)

    axis, angleY_to_rotate = get_angle_between_vectors_and_axis_to_rotate(z_c, z_global)
    mY = get_rotation_matrix_around_axis(axis, angleY_to_rotate)

    cs_moving = multiply_matrixes(mY, cs_moving)
    rotation_center_end_point = rotation_center_end_point.transform(mY)

    ### 4) итоговое вращение

    m_total_rotate = multiply_matrixes(multiply_matrixes(mX, mZ), mY)

    ### 5) линейное перемещение к центру

    vector_delta_translate = Vector3d.from_points(rotation_center_end_point, rotation_center_point)

    return (m_total_rotate, vector_delta_translate)





if __name__ == "__main__":
    global_angle = math.radians(225)

    globalX = Vector3d(1, 0, 0)

    print(f"globalX={globalX}")


    def rotateZ(phi):
        m = Matrix3x3()
        m.Xx = math.cos(phi)
        m.Yx = -math.sin(phi)
        m.Yy = math.cos(phi)
        m.Xy = math.sin(phi)
        m.Zz = 1
        return m


    localX = globalX.copy().transform(get_rotation_matrix_XYZ(0, 0, global_angle))
    print(f"localX ={localX}")
    localX = globalX.copy().transform(get_rotation_matrix_Euler(global_angle, 0, 0))
    print(f"localX ={localX}")
    localX = globalX.copy().transform(rotateZ(global_angle))
    print(f"localX ={localX}")

    axis, angle = get_angle_between_vectors_and_axis_to_rotate(localX, globalX)

    m_rotate = get_rotation_matrix_around_axis(axis, angle)

    result = localX.copy().transform(m_rotate)
    print(f"axis ={axis}")
    print(f"angle={angle}={math.degrees(angle)}°")
    print(f"result ={result}")
