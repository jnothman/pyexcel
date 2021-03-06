"""
    pyexcel.iterators
    ~~~~~~~~~~~~~~~~~~~

    Iterate through the two dimensional arrays

    :copyright: (c) 2014 by C. W.
    :license: GPL v3
"""
import re
import six
import copy

def _unique(seq):
    """
    Return a unique list of the incoming list
    
    Reference:
    http://stackoverflow.com/questions/480214/
    how-do-you-remove-duplicates-from-a-list-in-python-whilst-preserving-order
    """
    seen = set()
    seen_add = seen.add
    return [x for x in seq if not (x in seen or seen_add(x))]


def longest_row_number(array):
    """
    Find the length of the longest row in the array

    :param list in_array: a list of arrays    
    """
    if len(array) > 0:
        # map runs len() against each member of the array
        return max(map(len, array))
    else:
        return 0


def uniform(array):
    """
    Fill-in empty strings to empty cells to make it MxN

    :param list in_array: a list of arrays
    """
    width = longest_row_number(array)
    if width == 0:
        return array
    else:
        for row in array:
            row_length = len(row)
            if row_length < width:
                row += [""] * (width - row_length)
        return array

def transpose(in_array):
    """
    Rotate the array by 90 degrees

    :param list in_array: a list of arrays
    """
    max_length = longest_row_number(in_array)
    new_array = []
    for i in range(0, max_length):
        row_data = []
        for c in in_array:
            if i < len(c):
                row_data.append(c[i])
            else:
                row_data.append('')
        new_array.append(row_data)
    return new_array

"""
In order to easily compute the actual index of 'X' or 'AX', these utility
functions were written
"""

_INDICES = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

def _get_index(index_chars):
    length = len(index_chars)
    if len(index_chars) > 1:
        return (_get_index(index_chars[0])+1) * (len(_INDICES) ** (length-1)) + _get_index(index_chars[1:])
    else:
        return _INDICES.index(index_chars[0])

def _excel_column_index(index_chars):
    if len(index_chars) < 1:
        return -1
    else:
        return _get_index(index_chars.upper())

def _excel_cell_position(pos_chars):
    if len(pos_chars) < 2:
        return -1, -1
    group = re.match("([A-Za-z]+)([0-9]+)", pos_chars)
    if group:    
        return int(group.group(2)) - 1, _excel_column_index(group.group(1))
    else:
        raise IndexError
    
def _analyse_slice(aslice, upper_bound):
    """
    An internal function to analyze a given slice
    """
    if aslice.start is None:
        start = 0
    else:
        start = max(aslice.start, 0)
    if aslice.stop is None:
        stop = upper_bound
    else:
        stop = min(aslice.stop, upper_bound)
    if start > stop:
        raise ValueError
    elif start < stop:
        if aslice.step:
            my_range = range(start, stop, aslice.step)
        else:
            my_range = range(start, stop)
        if six.PY3:
            # for py3, my_range is a range object
            my_range = list(my_range)
    else:
        my_range = [start]
    return my_range


class Row:
    """
    Represet row of a matrix

    .. table:: "example.csv"

        = = =
        1 2 3
        4 5 6
        7 8 9
        = = =
    
    Above column manipluation can be performed on rows similiarly. This section will not repeat the same example but show some advance usages. 
    
        >>> import pyexcel as pe
        >>> reader = pe.Reader("example.csv")
        >>> reader.row[0:2]
        [[1, 4, 7], [2, 5, 8]]
        >>> reader.row[0:3] = [0, 0, 0]
        >>> reader.row[2]
        [0, 0, 0]
        >>> del reader.row[0:2]
        >>> reader.row[0]
        [0, 0, 0]

    """
    def __init__(self, matrix):
        self.ref = matrix

    def __delitem__(self, aslice):
        """Override the operator to delete items"""
        if isinstance(aslice, slice):
            my_range = _analyse_slice(aslice, self.ref.number_of_rows())
            self.ref.delete_rows(my_range)
        else:
            self.ref.delete_rows([aslice])

    def __setitem__(self, aslice, c):
        """Override the operator to set items"""
        if isinstance(aslice, slice):
            my_range = _analyse_slice(aslice, self.ref.number_of_rows())
            for i in my_range:
                self.ref.set_row_at(i, c)
        else:
            self.ref.set_row_at(aslice, c)

    def __getitem__(self, aslice):
        """By default, this class recognize from top to bottom
        from left to right"""
        index = aslice
        if isinstance(aslice, slice):
            my_range = _analyse_slice(aslice, self.ref.number_of_rows())
            results = []
            for i in my_range:
                results.append(self.ref.row_at(i))
            return results
        if index in self.ref.row_range():
            return self.ref.row_at(index)
        else:
            raise IndexError

    def __iadd__(self, other):
        """Overload += sign

        :return: self
        """
        if isinstance(other, list):
            self.ref.extend_rows(other)
        elif isinstance(other, Matrix):
            self.ref.extend_rows(other.array)
        else:
            raise TypeError
        return self

    def __add__(self, other):
        """Overload += sign

        :return: self
        """
        self.__iadd__(other)
        return self.ref


class Column:
    """
    Represet columns of a matrix
    
    .. table:: "example.csv"

        = = =
        1 2 3
        4 5 6
        7 8 9
        = = =
    
    Let us manipulate the data columns on the above data matrix::
    
        >>> import pyexcel as pe
        >>> reader = pe.Reader("example.csv")
        >>> reader.column[0]
        [1, 4, 7]
        >>> reader.column[2] = [0, 0, 0]
        >>> reader.column[2]
        [0, 0, 0]
        >>> del reader.column[2]
        >>> reader.column[2]
        [3, 6, 9]

    """
    def __init__(self, matrix):
        self.ref = matrix

    def __delitem__(self, aslice):
        """Override the operator to delete items"""
        if isinstance(aslice, slice):
            my_range = _analyse_slice(aslice, self.ref.number_of_columns())
            self.ref.delete_columns(my_range)
        elif isinstance(aslice, str):
            index = _excel_column_index(aslice)
            self.ref.delete_columns([index])
        elif isinstance(aslice, int):
            self.ref.delete_columns([aslice])
        else:
            raise IndexError

    def __setitem__(self, aslice, c):
        """Override the operator to set items"""
        if isinstance(aslice, slice):
            my_range = _analyse_slice(aslice, self.ref.number_of_columns())
            for i in my_range:
                self.ref.set_column_at(i, c)
        elif isinstance(aslice, str):
            index = _excel_column_index(aslice)
            self.ref.set_column_at(index, c)
        elif isinstance(aslice, int):
            self.ref.set_column_at(aslice, c)
        else:
            raise IndexError

    def __getitem__(self, aslice):
        """By default, this class recognize from top to bottom
        from left to right"""
        index = aslice
        if isinstance(aslice, slice):
            my_range = _analyse_slice(aslice, self.ref.number_of_columns())
            results = []
            for i in my_range:
                results.append(self.ref.column_at(i))
            return results
        elif isinstance(aslice, str):
            index = _excel_column_index(aslice)
        if index in self.ref.column_range():
            return self.ref.column_at(index)
        else:
            raise IndexError

    def __iadd__(self, other):
        """Overload += sign

        :return: self
        """
        if isinstance(other, list):
            self.ref.extend_columns(other)
        elif isinstance(other, Matrix):
            self.ref.extend_columns(other.array)
        else:
            raise TypeError
        return self

    def __add__(self, other):
        """Overload += sign

        :return: self
        """
        self.__iadd__(other)
        return self.ref


class Matrix:
    """
    The internal representation of a sheet data. Each element
    can be of any python types
    """
    
    def __init__(self, array):
        """Constructor

        The reason a deep copy was not made here is because
        the data sheet could be huge. It could be costly to
        copy every cell to a new memory area
        :param list array: a list of arrays
        """
        self.array = uniform(array)

    def number_of_rows(self):
        """The number of rows"""
        return len(self.array)

    def number_of_columns(self):
        """The number of columns"""
        if self.number_of_rows() > 0:
            return len(self.array[0])
        else:
            return 0

    def row_range(self):
        """
        Utility function to get row range
        """
        if six.PY2:
            return xrange(0, self.number_of_rows())
        else:
            return range(0, self.number_of_rows())

    def column_range(self):
        """
        Utility function to get column range
        """
        if six.PY2:
            return xrange(0, self.number_of_columns())
        else:
            return range(0, self.number_of_columns())

    def cell_value(self, row, column, new_value=None):
        """Random access to table cells

        :param int row: row index which starts from 0
        :param int column: column index which starts from 0
        :param any new_value: new value if this is to set the value
        """
        if new_value is None:
            if row in self.row_range() and column in self.column_range():
                # apply formatting
                return self.array[row][column]
            else:
                return None
        else:
            self.array[row][column] = new_value
            return new_value

    def __iter__(self):
        """
        Default iterator to go through each cell one by one from top row to
        bottom row and from left to right
        """
        return self.rows()

    def enumerate(self):
        """
        Default iterator to go through each cell one by one from top row to
        bottom row and from left to right
        example::
    
            import pyexcel as pe
            data = [  
                [1, 2, 3, 4],
                [5, 6, 7, 8],
                [9, 10, 11, 12]
            ]
            m = pe.Matrix(data)
            print(pe.utils.to_array(m.enumerate()))
    
        output::
        
            [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]

        More details see :class:`HTLBRIterator`
        """
        return HTLBRIterator(self)

    def reverse(self):
        """
        Reverse iterator to go through each cell one by one from
        bottom row to top row and from right to left
        example::
    
            import pyexcel as pe
            data = [  
                [1, 2, 3, 4],
                [5, 6, 7, 8],
                [9, 10, 11, 12]
            ]
            m = pe.Matrix(data)
            print(pe.utils.to_array(m.reverse()))
    
        output::
        
            [12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1]

        More details see :class:`HBRTLIterator`
        """
        return HBRTLIterator(self)

    def vertical(self):
        """
        Default iterator to go through each cell one by one from
        leftmost column to rightmost row and from top to bottom
        example::
    
            import pyexcel as pe
            data = [  
                [1, 2, 3, 4],
                [5, 6, 7, 8],
                [9, 10, 11, 12]
            ]
            m = pe.Matrix(data)
            print(pe.utils.to_array(m.vertical()))
    
        output::
        
            [1, 5, 9, 2, 6, 10, 3, 7, 11, 4, 8, 12]

        More details see :class:`VTLBRIterator`
        """
        return VTLBRIterator(self)

    def rvertical(self):
        """
        Default iterator to go through each cell one by one from rightmost
        column to leftmost row and from bottom to top
        example::
    
            import pyexcel as pe
            data = [  
                [1, 2, 3, 4],
                [5, 6, 7, 8],
                [9, 10, 11, 12]
            ]
            m = pe.Matrix(data)
            print(pe.utils.to_array(m.rvertical())
    
        output::
        
            [12, 8, 4, 11, 7, 3, 10, 6, 2, 9, 5, 1]

        More details see :class:`VBRTLIterator`
        """
        return VBRTLIterator(self)

    def rows(self):
        """
        Returns a top to bottom row iterator

        example::
    
            import pyexcel as pe
            data = [  
                [1, 2, 3, 4],
                [5, 6, 7, 8],
                [9, 10, 11, 12]
            ]
            m = pe.Matrix(data)
            print(pe.utils.to_array(m.rows()))
    
        output::
        
            [[1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11, 12]]

        More details see :class:`RowIterator`
        """
        return RowIterator(self)

    def rrows(self):
        """
        Returns a bottom to top row iterator
        
        example::
    
            import pyexcel as pe
            data = [  
                [1, 2, 3, 4],
                [5, 6, 7, 8],
                [9, 10, 11, 12]
            ]
            m = pe.Matrix(data)
            print(pe.utils.to_array(m.rrows()))
    
        output::
        
            [[9, 10, 11, 12], [5, 6, 7, 8], [1, 2, 3, 4]]

        More details see :class:`RowReverseIterator`
        """
        return RowReverseIterator(self)

    def columns(self):
        """
        Returns a left to right column iterator
      
        example::
    
            import pyexcel as pe
            data = [  
                [1, 2, 3, 4],
                [5, 6, 7, 8],
                [9, 10, 11, 12]
            ]
            m = pe.Matrix(data)
            print(pe.utils.to_array(m.columns()))
    
        output::
        
            [[1, 5, 9], [2, 6, 10], [3, 7, 11], [4, 8, 12]]

        More details see :class:`ColumnIterator`
        """
        return ColumnIterator(self)

    def rcolumns(self):
        """
        Returns a right to left column iterator
    
        example::
    
            import pyexcel as pe
            data = [  
                [1, 2, 3, 4],
                [5, 6, 7, 8],
                [9, 10, 11, 12]
            ]
            m = pe.Matrix(data)
            print(pe.utils.to_array(m.rcolumns()))
    
        output::
        
            [[4, 8, 12], [3, 7, 11], [2, 6, 10], [1, 5, 9]]

        More details see :class:`ColumnReverseIterator`
        """
        return ColumnReverseIterator(self)

    @property
    def row(self):
        return Row(self)

    @row.setter
    def row(self, value):
        # dummy setter to enable self.column += ..
        # in py3
        pass

    @property
    def column(self):
        return Column(self)

    @column.setter
    def column(self, value):
        # dummy setter to enable self.column += ..
        # in py3
        pass

    def row_at(self, index):
        """
        Gets the data at the specified row
        """
        if index in self.row_range():
            cell_array = []
            for i in self.column_range():
                cell_array.append(self.cell_value(index, i))
            return cell_array
        else:
            raise IndexError("Out of range")

    def column_at(self, index):
        """
        Gets the data at the specified column
        """
        if index in self.column_range():
            cell_array = []
            for i in self.row_range():
                cell_array.append(self.cell_value(i, index))
            return cell_array
        else:
            raise IndexError("Out of range")

    def set_column_at(self, column_index, data_array, starting=0):
        """Updates a column data range

        It works like this if the call is: set_column_at(2, ['N','N', 'N'], 1)::

                +--> column_index = 2
                |
            A B C
            1 3 N <- starting = 1
            2 4 N

        This function will not set element outside the current table range
        
        :param int column_index: which column to be modified
        :param list data_array: one dimensional array
        :param int staring: from which index, the update happens
        :raises IndexError: if column_index exceeds column range or starting exceeds row range
        """
        nrows = self.number_of_rows()
        ncolumns = self.number_of_columns()
        if column_index < ncolumns and starting < nrows:
            to = min(len(data_array)+starting, nrows)
            for i in range(starting, to):
                self.cell_value(i, column_index, data_array[i-starting])
        else:
            raise IndexError

    def set_row_at(self, row_index, data_array, starting=0):
        """Update a row data range

        It works like this if the call is: set_row_at(2, ['N', 'N', 'N'], 1)::

            A B C
            1 3 5 
            2 N N <- row_index = 2
              ^starting = 1
        
        This function will not set element outside the current table range
        
        :param int row_index: which row to be modified
        :param list data_array: one dimensional array
        :param int starting: from which index, the update happens
        :raises IndexError: if row_index exceeds row range or starting exceeds column range
        """
        nrows = self.number_of_rows()
        ncolumns = self.number_of_columns()
        if row_index < nrows and starting < ncolumns:
            to = min(len(data_array)+starting, ncolumns)
            for i in range(starting, to):
                self.cell_value(row_index, i, data_array[i-starting])
        else:
            raise IndexError

    def extend_rows(self, rows):
        """Inserts two dimensinal data after the bottom row"""
        array_length = self.number_of_columns()
        max_length = array_length
        for r in rows:
            length = len(r)
            agreed_length = max(length, array_length)
            if max_length < agreed_length:
                max_length = agreed_length
            array = copy.deepcopy(r[:agreed_length])
            if length < array_length:
                array = array + [""] * (array_length-length)
            self.array.append(array)
        # if number_of_rows > 0, means self has content
        # if self does not have content, does not make sense to
        # to increase width
        self.array = uniform(self.array)

    def delete_rows(self, row_indices):
        """Deletes specified row indices"""
        if isinstance(row_indices, list) is False:
            raise IndexError
        if len(row_indices) > 0:
            unique_list = _unique(row_indices)
            sorted_list = sorted(unique_list, reverse=True)
            for i in sorted_list:
                if i < self.number_of_rows():
                    del self.array[i]

    def extend_columns(self, columns):
        """Inserts two dimensional data after the rightmost column

        This is how it works:

        Given::
        
            s s s     t t

        Get::
        
            s s s  +  t t
        """
        current_nrows = self.number_of_rows()
        current_ncols = self.number_of_columns()
        insert_column_nrows = len(columns)
        array_length = min(current_nrows, insert_column_nrows)
        for i in range(0, array_length):
            array = copy.deepcopy(columns[i])
            self.array[i] += array
        if current_nrows < insert_column_nrows:
            delta = insert_column_nrows - current_nrows
            base = current_nrows
            for i in range(0, delta):
                new_array = [""] * current_ncols
                new_array += columns[base+i]
                self.array.append(new_array)
        self.array = uniform(self.array)

    def delete_columns(self, column_indices):
        """Delete columns by specified list of indices
        """
        if isinstance(column_indices, list) is False:
            raise ValueError
        if len(column_indices) > 0:
            unique_list = _unique(column_indices)
            sorted_list = sorted(unique_list, reverse=True)
            for i in range(0, len(self.array)):
                for j in sorted_list:
                    del self.array[i][j]

    def __setitem__(self, aset, c):
        """Override the operator to set items"""
        if isinstance(aset, tuple):
            return self.cell_value(aset[0], aset[1], c)
        elif isinstance(aset, str):
            row, column = _excel_cell_position(aset)
            return self.cell_value(row, column, c)
        else:
            raise IndexError

    def __getitem__(self, aset):
        """By default, this class recognize from top to bottom
        from left to right"""
        if isinstance(aset, tuple):
            return self.cell_value(aset[0], aset[1])
        elif isinstance(aset, str):
            row, column = _excel_cell_position(aset)
            return self.cell_value(row, column)
        elif isinstance(aset, int):
            print("Deprecated usage. Please use [row, column]")
            return self.row_at(aset)
        else:
            raise IndexError

    def contains(self, predicate):
        """Has something in the table"""
        for r in self.rows():
            if predicate(r):
                return True
        else:
            return False

    def transpose(self):
        """Roate the data table by 90 degrees

        Reference :func:`transpose`
        """
        self.array = transpose(self.array)

    def to_array(self):
        """Get an array out
        """
        return self.array


class PyexcelIterator:
    """
    A parent class is used to distiguish pyexcel iterators in pyexcel utilities
    """
    def __next__(self):
        return self.next()
    pass


class HTLBRIterator(PyexcelIterator):
    """
    Horizontal Top Left to Bottom Right Iterator
    
    Iterate horizontally from top left to bottom right.
    see :func:`Matrix.enumerate` for more details
    """
    def __init__(self, reader):
        self.reader_ref = reader
        self.current = 0
        self.columns = reader.number_of_columns()
        self.rows = reader.number_of_rows()
        self.total = self.columns * self.rows

    def __iter__(self):
        return self

    def next_cell_position(self):
        """
        Determine next cell position
        """
        return (int(self.current / self.columns),
                int(self.current % self.columns))

    def move_cursor(self):
        """
        move internal cursor
        """
        self.current += 1

    def get_next_value(self):
        """
        Get next value
        """
        row, column = self.next_cell_position()
        self.move_cursor()
        return self.reader_ref.cell_value(row, column)

    def exit_condition(self):
        """
        Determine if all data have been iterated
        """
        return self.current >= self.total

    def next(self):
        """
        determine next value

        this function is further divided into small functions
        so that other kind of iterators can easily change
        its behavior
        """
        if self.exit_condition():
            raise StopIteration
        else:
            return self.get_next_value()


class VTLBRIterator(HTLBRIterator):
    """
    Vertical Top Left to Bottom Right Iterator

    Iterate vertically from top left to bottom right
    see :func:`Matrix.vertical` for more details
    """
    def next_cell_position(self):
        """
        this function controls the iterator's path
        """
        return (int(self.current % self.rows),
                int(self.current / self.rows))


class HBRTLIterator(HTLBRIterator):
    """
    Horizontal Bottom Right to Top Left Iterator
    
    Iterate horizontally from bottom right to top left
    see :func:`Matrix.reverse` for more details
    """

    def __init__(self, reader):
        self.reader_ref = reader
        self.columns = reader.number_of_columns()
        self.rows = reader.number_of_rows()
        self.current = self.rows * self.columns

    def exit_condition(self):
        return self.current <= 0

    def move_cursor(self):
        self.current -= 1

    def get_next_value(self):
        self.move_cursor()
        row, column = self.next_cell_position()
        return self.reader_ref.cell_value(row, column)


class VBRTLIterator(HBRTLIterator):
    """
    Vertical Bottom Right to Top Left Iterator
    
    Iterate vertically from bottom right to top left
    see :func:`Matrix.rvertical` for more details
    """
    def next_cell_position(self):
        return (int(self.current % self.rows),
                int(self.current / self.rows))


class HTRBLIterator(PyexcelIterator):
    """
    Horizontal Top Right to Bottom Left Iterator

    Iterate horizontally from top right to bottom left::
    
        <<S
        <<<
        E<<
    """
    def __init__(self, reader):
        self.reader_ref = reader
        self.columns = reader.number_of_columns()
        self.rows = reader.number_of_rows()
        self.total = self.rows * self.columns
        self.row = 0
        self.column = self.columns

    def __iter__(self):
        return self

    def get_next_value(self):
        self.column -= 1
        if self.column == -1:
            self.column = self.columns - 1
            self.row += 1
        return self.reader_ref.cell_value(self.row, self.column)

    def exit_condition(self):
        return self.column == 0 and self.row == (self.rows - 1)

    def next(self):
        if self.exit_condition():
            raise StopIteration
        else:
            return self.get_next_value()


class VTRBLIterator(HTRBLIterator):
    """
    Vertical Top Right to Bottom Left Iterator

    Iterate horizontally from top left to bottom right::
    
        ||S
        |||
        E||
    """
    def __init__(self, reader):
        self.reader_ref = reader
        self.columns = reader.number_of_columns()
        self.rows = reader.number_of_rows()
        self.total = self.rows * self.columns
        self.row = -1
        self.column = self.columns - 1

    def get_next_value(self):
        self.row += 1
        if self.row >= self.rows:
            self.column -= 1
            self.row = 0
        return self.reader_ref.cell_value(self.row, self.column)


class VBLTRIterator(HTRBLIterator):
    """
    Vertical Bottom Left to Top Right Iterator

    Iterate vertically from bottom left to top right::
    
        ^^E
        ^^^
        S^^
        ->
    """
    def __init__(self, reader):
        self.reader_ref = reader
        self.columns = reader.number_of_columns()
        self.rows = reader.number_of_rows()
        self.total = self.rows * self.columns
        self.row = self.rows
        self.column = 0

    def __iter__(self):
        return self

    def get_next_value(self):
        self.row -= 1
        if self.row == -1:
            self.row = self.rows - 1
            self.column += 1
        return self.reader_ref.cell_value(self.row, self.column)

    def exit_condition(self):
        return self.row == 0 and self.column == (self.columns - 1)


class HBLTRIterator(VBLTRIterator):
    """
    Horizontal Bottom Left to Top Right Iterator

    Iterate horizontally from bottom left to top right::
    
        >>E
        >>> ^
        S>> |
    """
    def __init__(self, reader):
        self.reader_ref = reader
        self.columns = reader.number_of_columns()
        self.rows = reader.number_of_rows()
        self.total = self.rows * self.columns
        self.row = self.rows - 1
        self.column = -1

    def __iter__(self):
        return self

    def get_next_value(self):
        self.column += 1
        if self.column >= self.columns:
            self.row -= 1
            self.column = 0
        return self.reader_ref.cell_value(self.row, self.column)


class RowIterator(PyexcelIterator):
    """
    Iterate data row by row from top to bottom

    default iterator for :class:`Matrix`.
    See :func:`Matrix.rows` for more details
    """
    def __init__(self, reader):
        self.reader_ref = reader
        self.current = 0

    def __iter__(self):
        return self

    def next(self):
        if self.current in self.reader_ref.row_range():
            row = self.current
            self.current += 1
            return self.reader_ref.row_at(row)
        else:
            raise StopIteration


class RowReverseIterator(PyexcelIterator):
    """
    Iterate data row by row from bottom to top

    see :func:`Matrix.rrows` for more details
    """
    def __init__(self, reader):
        self.reader_ref = reader
        self.current = reader.number_of_rows() - 1

    def __iter__(self):
        return self

    def next(self):
        if self.current in self.reader_ref.row_range():
            self.current -= 1
            return self.reader_ref.row_at(self.current+1)
        else:
            raise StopIteration


class ColumnIterator(PyexcelIterator):
    """
    Column Iterator from left to right
    
    see :func:`Matrix.columns` for more details
    """
    def __init__(self, reader):
        self.reader_ref = reader
        self.current = 0

    def __iter__(self):
        return self

    def next(self):
        if self.current in self.reader_ref.column_range():
            self.current += 1
            return self.reader_ref.column_at(self.current-1)
        else:
            raise StopIteration


class ColumnReverseIterator(PyexcelIterator):
    """
    Column Reverse Iterator from right to left

    see :func:`Matrix.rcolumns` for more details
    """
    def __init__(self, reader):
        self.reader_ref = reader
        self.current = reader.number_of_columns() - 1

    def __iter__(self):
        return self

    def next(self):
        if self.current in self.reader_ref.column_range():
            self.current -= 1
            return self.reader_ref.column_at(self.current+1)
        else:
            raise StopIteration


class ColumnIndexIterator(PyexcelIterator):
    """
    Column Iterator

    Default iterator for :class:`Sheet` when it becomes Series
    See :func:`Sheet.__iter__` for more details
    """
    def __init__(self, reader):
        self.reader_ref = reader
        self.current = 0

    def __iter__(self):
        return self

    def next(self):
        if self.current in self.reader_ref.column_range():
            index = self.current
            self.current += 1
            column_header = self.reader_ref.colnames[index]
            return {column_header: self.reader_ref.named_column_at(column_header)}
        else:
            raise StopIteration


class RowIndexIterator(PyexcelIterator):
    """
    Row Iterator

    Default iterator for :class:`Sheet` when it becomes Series
    See :func:`Sheet.__iter__` for more details
    """
    def __init__(self, reader):
        self.reader_ref = reader
        self.current = 0

    def __iter__(self):
        return self

    def next(self):
        if self.current in self.reader_ref.row_range():
            index = self.current
            self.current += 1
            column_header = self.reader_ref.rownames[index]
            return {column_header: self.reader_ref.named_row_at(column_header)}
        else:
            raise StopIteration


class SheetIterator(PyexcelIterator):
    """
    Sheet Iterator
    """
    def __init__(self, bookreader):
        self.book_reader_ref = bookreader
        self.current = 0

    def __iter__(self):
        return self

    def next(self):
        if self.current < self.book_reader_ref.number_of_sheets():
            self.current += 1
            return self.book_reader_ref[self.current-1]
        else:
            raise StopIteration
