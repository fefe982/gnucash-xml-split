import decimal
import gzip
from xml.etree import ElementTree


class Account(object):
    def __init__(self, name, guid, actype, parent=None, commodity=None, description=None, name_full=None):
        self.name = name
        self.guid = guid
        self.actype = actype
        self.description = description
        self.parent = parent
        self.commodity = commodity
        self.name_full = name_full
        self.balance = decimal.Decimal(0)

    def __repr__(self):
        return "<Account {}>".format(self.guid)


def getElementText(element: ElementTree.Element, tag: str) -> str:
    child = element.find(tag)
    assert child is not None, "Element {} not found in {}".format(tag, element.tag)
    assert child.text is not None, "Element {} has no text".format(tag)
    return child.text


def getElementTreeFromFile(file: str):
    tree = ElementTree.parse(gzip.open(file, "rb"))
    root = tree.getroot()
    if root.tag != "gnc-v2":
        raise ValueError("File stream was not a valid GNU Cash v2 XML file")
    return tree


for ns in ["gnc", "cd", "book", "slot", "cmdty", "price", "ts", "act", "trn", "split"]:
    ElementTree.register_namespace(ns, "http://www.gnucash.org/XML/" + ns)
