import re
from typing import Callable
from collections import UserDict
import datetime
from typing import Optional

class Field:
    def __init__(self, value: str):
        self.value = value

    def __str__(self) -> str:
        return str(self.value)


class Name(Field):
    def __init__(self, value):
        super().__init__(value)


class Birthday(Field):
    def __init__(self, value):
        super().__init__(value)
        try:
            datetime_str = datetime.datetime.strptime(value, '%d.%m.%Y')
        except ValueError:
            raise ValueError("Invalid date format. Use DD.MM.YYYY")
        self.value = datetime_str

class Phone(Field):
    def __init__(self, value: str):
        super().__init__(self._validate(value))

    @staticmethod
    def _validate(value: str) -> str:
        if not isinstance(value, str):
            raise TypeError("Phone number must be a string")
        digits = ''.join(ch for ch in value if ch.isdigit())
        if len(digits) != 10:
            raise ValueError("Phone number must have 10 digits")
        return value

class Record:
    def __init__(self, name):
        self.name = Name(name)
        self.phones = []
        self.birthday = None

    def add_phone(self, phone: str | Phone) -> Phone:
        phone_instance = phone if isinstance(phone, Phone) else Phone(phone)
        self.phones.append(phone_instance)
        return phone_instance

    def remove_phone(self, phone: str | Phone) -> bool:
        phone_instance = phone if isinstance(phone, Phone) else Phone(phone)
        if phone_instance in self.phones:
            self.phones.remove(phone_instance)
            return True
        return False

    def edit_phone(self, old_phone: str | Phone, new_phone: str | Phone) -> bool:
        old_instance = old_phone if isinstance(old_phone, Phone) else Phone(old_phone)
        new_instance = new_phone if isinstance(new_phone, Phone) else Phone(new_phone)
        for i, p in enumerate(self.phones):
            if old_instance == p:
                self.phones[i] = new_instance
                return True
        return False

    def find_phone(self, phone: str | Phone) -> Optional[Phone]:
        phone_instance = phone if isinstance(phone, Phone) else Phone(phone)
        for i, p in enumerate(self.phones):
            if phone_instance == p:
                return self.phones[i]
        return None

    def add_birthday(self, birthday: str | Birthday):
        birthday_obj = birthday if isinstance(birthday, Birthday) else Birthday(birthday)
        self.birthday = birthday_obj

    def __str__(self):
        bday = self.birthday.value.strftime("%d.%m.%Y") if self.birthday else "-"
        phones = '; '.join(p.value for p in self.phones)
        return f"Contact name: {self.name.value}, phones: {phones}, birthday: {bday}"

class AddressBook(UserDict):

    def add_record(self, record: Record) -> None:
        if not isinstance(record, Record):
            raise TypeError("Очікувався об'єкт Record.")
        key = record.name.value
        self.data[key] = record

    def find(self, name: str) -> Optional[Record]:
        return self.data.get(name)


    def delete(self, name: str) -> bool:
        if name in self.data:
            del self.data[name]
            return True
        return False

    def get_upcoming_birthdays(self):
        today = datetime.datetime.today().date()
        upcoming = []

        for record in self.data.values():
            if not record.birthday:
                continue

            bday_date = record.birthday.value.date()  # datetime -> date
            bday_this_year = bday_date.replace(year=today.year)

            if bday_this_year < today:
                bday_this_year = bday_this_year.replace(year=today.year + 1)

            delta_days = (bday_this_year - today).days
            if 0 <= delta_days <= 7:
                congratulation_date = bday_this_year
                if congratulation_date.weekday() == 5:  # Saturday
                    congratulation_date += datetime.timedelta(days=2)
                elif congratulation_date.weekday() == 6:  # Sunday
                    congratulation_date += datetime.timedelta(days=1)

                upcoming.append({
                    "name": record.name.value,
                    "congratulation_date": congratulation_date.strftime("%d.%m.%Y")
                })
        return upcoming


def input_error(func: Callable):
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValueError:
            return "Give me name and phone please."
        except KeyError:
            return "Contact not found."
        except IndexError:
            return "Enter user name."
    return inner

def parse_input(user_input):
    cmd, *args = user_input.split()
    cmd = cmd.strip().lower()
    return cmd, *args

@input_error
def add_contact(args, book: AddressBook):
    name, phone, *_ = args
    record = book.find(name)
    msg = "Contact updated."
    if record is None:
        record = Record(name)
        book.add_record(record)
        msg = "Contact added."
    if phone:
        record.add_phone(phone)
    return msg

def validate_phone(phone):
    UA_SIMPLE = re.compile(r'^(?:\+?380|0)\d{9}$')
    if not phone.isdigit():
        return False
    if not UA_SIMPLE.match(phone):
        return False
    return True

@input_error
def get_contact_phone(args, book: AddressBook):
    name = args[0]
    record = book.find(name)
    if record is None:
        return "Contact not found."
    return "; ".join(p.value for p in record.phones) or "No phones."

@input_error
def print_all_contacts(book: AddressBook):
    for record in book.data.values():
        print(record)

@input_error
def update_contact(args, book: AddressBook):
    name, old_phone, new_phone = args
    if not validate_phone(new_phone):
        return "Invalid phone format."

    record = book.find(name)
    if record is None:
        raise ValueError(f"Contact with name={name} not found.")
    record.edit_phone(old_phone, new_phone)
    return None

@input_error
def add_birthday(args, book: AddressBook) -> Record | None:
    name, birthday = args
    record = book.find(name)
    if record is None:
        raise ValueError("Contact not found.")
    record.add_birthday(birthday)
    return record

@input_error
def show_birthday(args, book: AddressBook):
    name = args[0]
    record = book.find(name)
    if record is None or record.birthday is None:
        raise ValueError("Contact not found or birthday not set.")
    print(record.birthday.value.strftime("%d.%m.%Y"))

def main():
    book = AddressBook()
    print("Welcome to the assistant bot!")
    while True:
        user_input = input("Enter a command: ")
        command, *args = parse_input(user_input)

        match command:
            case "close" | "exit":
                print("Good bye!")
                return
            case "hello":
                print("How can I help you?")
            case "add":
                result = add_contact(args, book)
                if result:
                    print(result)
            case "change":
                result = update_contact(args, book)
                if result:
                    print(result)
            case "phone":
                result = get_contact_phone(args, book)
                if result:
                    print(result)
            case "all":
                print_all_contacts(book)
            case "add-birthday":
                add_birthday(args, book)
            case "show-birthday":
                show_birthday(args, book)
            case "birthdays":
                print(book.get_upcoming_birthdays())
            case _:
                print("Invalid command.")

if __name__ == "__main__":
    main()
