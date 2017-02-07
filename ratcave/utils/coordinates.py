import numpy as np
import _transformations as trans
from abc import ABCMeta, abstractmethod
from .observers import IterObservable


class Coordinates(IterObservable):

    def __init__(self, *args, **kwargs):
        super(Coordinates, self).__init__(**kwargs)
        self._array = np.array(args, dtype=np.float32)

    def __repr__(self):
        arg_str = ', '.join(['{}={}'.format(*el) for el in zip('xyz', self._array)])
        return "{cls}({coords})".format(cls=self.__class__.__name__, coords=arg_str)

    def __getitem__(self, item):
        if type(item) == slice:
            return tuple(self._array[item])
        else:
            return self._array[item]

    def __setitem__(self, idx, value):
        super(Coordinates, self).__setitem__(idx, value)
        self._array[idx] = value

    # Note: Index counts backwards from end of array to increase compatibility with Quaternions.
    @property
    def x(self):
        return self[-3]

    @x.setter
    def x(self, value):
        self[-3] = value

    @property
    def y(self):
        return self[-2]

    @y.setter
    def y(self, value):
        self[-2] = value

    @property
    def z(self):
        return self[-1]

    @z.setter
    def z(self, value):
        self[-1] = value

    @property
    def xyz(self):
        return self[-3:]

    @xyz.setter
    def xyz(self, value):
        self[-3:] = value


class RotationBase(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def to_quaternion(self): pass

    @abstractmethod
    def to_euler(self, units='rad'): pass

    @abstractmethod
    def to_matrix(self): pass

    @classmethod
    def from_matrix(cls, matrix): pass

    def rotate(self, vector):
        """Takes a vector and returns it rotated by self."""
        return np.dot(self.to_matrix()[:3, :3], vector).flatten()


class RotationEuler(RotationBase, Coordinates):

    axes = 'rxyz'

    def __init__(self, x, y, z, **kwargs):
        super(RotationEuler, self).__init__(x, y, z, **kwargs)


class RotationEulerRadians(RotationEuler):

    def to_radians(self):
        return self

    def to_degrees(self):
        return RotationEulerDegrees(*np.degrees(self._array))

    def to_quaternion(self):
        return RotationQuaternion(*trans.quaternion_from_euler(*self._array, axes=self.axes))

    def to_matrix(self):
        return trans.euler_matrix(*self._array, axes=self.axes)

    def to_euler(self, units='rad'):
        assert units.lower() in ['rad', 'deg']
        if units.lower() == 'rad':
            return RotationEulerRadians(*self._array)
        else:
            return RotationEulerDegrees(*np.degrees(self._array))

    @classmethod
    def from_matrix(cls, matrix):
        # Change to 4x4 if 3x3 rotation matrix is given
        if matrix.shape[0] == 3:
            mat = np.identity(4)
            mat[:3, :3] = matrix
            matrix = mat
        coords = trans.euler_from_matrix(matrix, axes=cls.axes)
        return cls(*coords)



class RotationEulerDegrees(RotationEuler):
    def to_radians(self):
        return RotationEulerRadians(*np.radians(self._array))

    def to_degrees(self):
        return self

    def to_quaternion(self):
        return self.to_radians().to_quaternion()

    def to_euler(self, units='rad'):
        return self.to_radians().to_euler(units=units)

    def to_matrix(self):
        return self.to_radians().to_matrix()

    @classmethod
    def from_matrix(cls, matrix):
        # Change to 4x4 if 3x3 rotation matrix is given
        if matrix.shape[0] == 3:
            mat = np.identity(4)
            mat[:3, :3] = matrix
            matrix = mat
        coords = trans.euler_from_matrix(matrix, axes=cls.axes)
        return cls(*np.degrees(coords))


class RotationQuaternion(RotationBase, Coordinates):

    def __init__(self, w, x, y, z, **kwargs):
        super(RotationQuaternion, self).__init__(w, x, y, z)

    def __repr__(self):
        arg_str = ', '.join(['{}={}'.format(*el) for el in zip('wxyz', self._array)])
        return "{cls}({coords})".format(cls=self.__class__.__name__, coords=arg_str)

    def to_quaternion(self):
        return self

    def to_matrix(self):
        return trans.quaternion_matrix(self._array)

    def to_euler(self, units='rad'):
        euler_data = trans.euler_from_matrix(self.to_matrix(), axes=RotationEuler.axes)
        assert units.lower() in ['rad', 'deg']
        if units.lower() == 'rad':
            return RotationEulerRadians(*euler_data)
        else:
            return RotationEulerDegrees(*np.degrees(euler_data))

    @classmethod
    def from_matrix(cls, matrix):
        # Change to 4x4 if 3x3 rotation matrix is given
        if matrix.shape[0] == 3:
            mat = np.identity(4)
            mat[:3, :3] = matrix
            matrix = mat
        coords = trans.quaternion_from_matrix(matrix)
        return cls(*coords)

    @property
    def w(self):
        return self[-4]

    @w.setter
    def w(self, value):
        self[-4] = value

    @property
    def wxyz(self):
        return self[-4:]

    @wxyz.setter
    def wxyz(self, value):
        self[-4:] = value

    @property
    def xyzw(self):
        return self[[1, 2, 3, 0]]

    @xyzw.setter
    def xyzw(self, value):
        self[[1, 2, 3, 0]] = value


class Translation(Coordinates):

    def __init__(self, *args, **kwargs):
        assert len(args) == 3, "Must be xyz coordinates"
        super(Translation, self).__init__(*args, **kwargs)

    def to_matrix(self):
        return trans.translation_matrix(self._array)


class Scale(Coordinates):

    def to_matrix(self):
        return trans.scale_matrix(self._array[0])

    @property
    def y(self):
        return self[0]

    @y.setter
    def y(self, value):
        self[0] = value

    @property
    def z(self):
        return self[0]

    @z.setter
    def z(self, value):
        self[0] = value

    @property
    def xyz(self):
        return self[0]

    @xyz.setter
    def xyz(self, value):
        if hasattr(value, '__iter__'):
            assert value[0] == value[1] == value[2], "Scale doesn't yet support differing dimension values."
            self[0] = value[0]
        else:
            self[0] = value


