import argparse
import decimal
import gzip
import datetime
from collections import defaultdict
from xml.etree import ElementTree

parser = argparse.ArgumentParser(description='GnuCash XML Splitter')
parser.add_argument('-i','--input', help='input file name',required=True)
parser.add_argument('-o','--output',help='output file name', required=True)
parser.add_argument('-y','--year', help='year of the transations to extract', required=True)
args = parser.parse_args()


class Account(object):
    def __init__(self, name, guid, actype, parent=None,
    commodity=None, description=None, name_full=None):
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
    def find_account(self, name):
        for account, children, splits in self.walk():
            if account.name == name:
                return account

 
xmltree = ElementTree.parse(gzip.open(args.input, "rb"))
root = xmltree.getroot()
if root.tag != 'gnc-v2':
    raise ValueError("File stream was not a valid GNU Cash v2 XML file")

for ns in ["gnc", "cd", "book", "slot", "cmdty", "price", "ts", "act", "trn", "split"]:
    ElementTree.register_namespace(ns, "http://www.gnucash.org/XML/" + ns)

dtfrom = datetime.datetime.strptime(args.year + "-01-01 00:00:00", '%Y-%m-%d %H:%M:%S')
dtto = datetime.datetime.strptime(args.year + "-12-31 23:59:59", '%Y-%m-%d %H:%M:%S')

i = 0
for book in root.findall('./{http://www.gnucash.org/XML/gnc}book'):
    accountdict = {}
    for account in book.findall('{http://www.gnucash.org/XML/gnc}account'):
        name = account.find('{http://www.gnucash.org/XML/act}name').text
        guid = account.find('{http://www.gnucash.org/XML/act}id').text
        actype = account.find('{http://www.gnucash.org/XML/act}type').text
        description = account.find('{http://www.gnucash.org/XML/act}description')
        if description is not None:
            description = description.text
        if actype == 'ROOT':
            parent = None
            commodity = None
        else:
            parent = account.find('{http://www.gnucash.org/XML/act}parent').text
            commodity = account.find('{http://www.gnucash.org/XML/act}commodity/{http://www.gnucash.org/XML/cmdty}id').text
        accountdict[guid] = Account(name=name,
                description=description,
                guid=guid,
                parent=parent,
                actype=actype,
                commodity=commodity)
    for acc_key in accountdict:
        account = accountdict[acc_key]
        if account.actype == 'ROOT':
            account.name_full = ''
        else:
            ancestor = [account, accountdict[account.parent]]
            while len(ancestor) > 1:
                ances = ancestor[-1];
                curr = ancestor[-2];
                if ances.actype == 'ROOT':
                    curr.name_full = curr.name
                    ancestor.pop()
                elif ances.name_full is not None:
                    curr.name_full = ances.name_full + ':' + curr.name
                    ancestor.pop()
                else:
                    ancestor.append(accountdict[ances.parent])
    for transaction in book.findall('./{http://www.gnucash.org/XML/gnc}transaction'):
        datestr = transaction.find('./{http://www.gnucash.org/XML/trn}date-posted/{http://www.gnucash.org/XML/ts}date').text
        dt = datetime.datetime.strptime(datestr, '%Y-%m-%d %H:%M:%S %z').replace(tzinfo=None)
        if dt >= dtfrom and dt <= dtto:
            i = i + 1
        else:
            if dt < dtfrom:
                for split in transaction.findall('{http://www.gnucash.org/XML/trn}splits/{http://www.gnucash.org/XML/trn}split'):
                    quantity = split.find("{http://www.gnucash.org/XML/split}quantity").text
                    account = accountdict[split.find("{http://www.gnucash.org/XML/split}account").text]
                    num, denom = quantity.split("/")
                    account.balance = account.balance + decimal.Decimal(num) / decimal.Decimal(denom)
            book.remove(transaction)
    for count in book.findall('{http://www.gnucash.org/XML/gnc}count-data'):
        if count.get('{http://www.gnucash.org/XML/cd}type') == 'transaction':
            count.text = str(i)
    balancedict = defaultdict(list)
    for acc_key in accountdict:
        account = accountdict[acc_key]
        if account.actype != 'ROOT' and account.actype != 'INCOME' and account.actype != 'EXPENSE' and account.actype != 'EQUITY' and account.balance != 0:
            balancedict[account.commodity].append(account)
    for cmdy_key in balancedict:
        f = open (args.year + cmdy_key + '.qif', 'w', encoding='utf-8');
        print('!Account', file=f)
        print('NEquity:Opening Balances:'+cmdy_key, file=f)
        print('TOth A', file=f)
        print('^', file=f)
        print('!Type:Oth A', file=f)
        print('D' + args.year + '-01-01', file=f)
        for account in balancedict[cmdy_key]:
            print('S' + account.name_full, file=f)
            print('$' + str(-account.balance), file=f)
        print('^', file=f)
        f.close()
xmltree.write(args.output, encoding="utf8")
