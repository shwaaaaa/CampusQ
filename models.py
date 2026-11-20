"""OOP models: Person (parent), Student and Staff (children)."""


class Person:
    def __init__(self, person_id, name):
        self._id = person_id          # encapsulated (read via property)
        self._name = name

    @property
    def id(self):
        return self._id

    @property
    def name(self):
        return self._name

    def show_info(self):
        return f"{self._id} - {self._name}"


class Student(Person):
    def __init__(self, student_id, name, course, year):
        super().__init__(student_id, name)
        self.course = course
        self.year = year

    def show_info(self):              # polymorphism
        return f"Student {self._id}: {self._name} ({self.course}, Year {self.year})"


class Staff(Person):
    def __init__(self, staff_id, name, department):
        super().__init__(staff_id, name)
        self.department = department

    def show_info(self):              # polymorphism
        return f"Staff {self._id}: {self._name} ({self.department})"
