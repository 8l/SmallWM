"""
Useful, general functions and constants used in various places throughout
SmallWM.
"""

from Xlib import X

# These are the minimum and maximum layers which are made available to users
MIN_LAYER = 1
MAX_LAYER = 9

# The default layer for clients to appear at
DEFAULT_LAYER = 5

def positive_int(text):
    """
    Converts a str into a positive int - if the str is not a valid number, or
    the int is not positive, this raises a ValueError.
    """
    value = int(text, 0)
    if value <= 0:
        raise ValueError
    return value

class BijectiveSetMapping:
    """
    The name is, admittedly, confusing - however, my best explanation follows.

    In :class:`~smallwm.client_data.ClientData`, there is a storage dynamic
    which looks like the following:::

        +------------+
        | DESKTOP_ALL|---------> A
        +------------+    |
                          +----> B

        +--------------+
        | DESKTOP_ICON |-------> C
        +--------------+  |
                          +----> D

        ...

    As you can see, there is essentially a mapping between a desktop and all of
    the clients in that desktop - it is essentially a set of trees. The big
    constraint is that no client can belong to more than one branch of the
    tree at one time. 
    
    A similar pattern follows for mapping layers to the list of clients in that
    layer.

    This class is provided to make operating on this style of data easy and
    efficient, by allowing for easy two-way lookups and other operations.
    """
    def __init__(self, *categories):
        # Categories are the "parent nodes" which hold other elements. This is
        # a 1-to-many relation.
        self._categories = {category: set() for category in categories}
        # Elements are the children of categories. This is a 1-to-1 relation.
        self._elements = {}

    def is_element(self, element):
        """
        :param element: A potential element.
        :return: ``True`` if the element exists, ``False`` otherwise.
        """
        return element in self._elements

    def is_category(self, category):
        """
        :param category: A potential category.
        :return: ``True`` if the category exists, ``False`` otherwise.
        """
        return category in self._categories

    def categories(self):
        """
        :return: The set of categories.
        """
        return set(self._categories.keys())

    def elements(self):
        """
        :return: The set of elements.
        """
        return set(self._elements.keys())

    def get_category_of(self, element):
        """
        :param element: An element.
        :return: The category which the given element occupies.
        :raises KeyError: If the element does not exit.
        """
        return self._elements[element]

    def get_elements_of(self, *categories):
        """
        :param category: A category.
        :return: A copy of the elements in that category.
        :raises KeyError: If the category does not exist.
        """
        final_set = set()
        for category in categories:
            final_set |= self._categories[category]
        return final_set

    def count_elements_of(self, category):
        """
        :param category: A category.
        :return: The number of elements in that category.
        :raises KeyError: If the category does not exist.
        """
        return len(self._categories[category])

    def add(self, category, element):
        """
        Adds an element to a category.

        :param category: The category to add into.
        :param element: The element to add.
        :raises KeyError: If the category does not exist.
        :raises KeyError: If the element is already in another category.
        """
        if element in self._elements:
            raise KeyError('{} is already present'.format(element))

        self._categories[category].add(element)
        self._elements[element] = category

    def move(self, element, to_category):
        """
        Moves an element over to another category.

        :param element: The element to move.
        :param to_category: The category to move into.
        :raises KeyError: If the element does not exist.
        :raises KeyError: If the receiving category does not exist.
        """
        self.remove(element)
        self.add(to_category, element)

    def remove(self, element):
        """
        Removes an element from whatever category it resides in.
        
        :param element: The element to remove.
        :raises KeyError: If the element does not exist.
        """
        category = self._elements[element]
        del self._elements[element]
        self._categories[category].remove(element)
