import argparse
import datetime
import decimal
from collections import defaultdict

import gnucash_base as gb

parser = argparse.ArgumentParser(description="GnuCash XML Splitter")
parser.add_argument("-i", "--input", help="input file name", required=True)
parser.add_argument("-o", "--output", help="output file name", required=True)
parser.add_argument("-y", "--year", help="year of the transations to extract", required=True)
args = parser.parse_args()


xmltree = gb.getElementTreeFromFile(args.input)
root = xmltree.getroot()


dtfrom = datetime.datetime.strptime(args.year + "-01-01 00:00:00", "%Y-%m-%d %H:%M:%S")
dtto = datetime.datetime.strptime(args.year + "-12-31 23:59:59", "%Y-%m-%d %H:%M:%S")

i = 0
for book in root.findall("./{http://www.gnucash.org/XML/gnc}book"):
    accountdict = {}
    for account in book.findall("{http://www.gnucash.org/XML/gnc}account"):
        name = gb.getElementText(account, "{http://www.gnucash.org/XML/act}name")
        guid = gb.getElementText(account, "{http://www.gnucash.org/XML/act}id")
        actype = gb.getElementText(account, "{http://www.gnucash.org/XML/act}type")
        description = account.find("{http://www.gnucash.org/XML/act}description")
        if description is not None:
            description = description.text
        if actype == "ROOT":
            parent = None
            commodity = None
        else:
            parent = gb.getElementText(account, "{http://www.gnucash.org/XML/act}parent")
            commodity = gb.getElementText(
                account, "{http://www.gnucash.org/XML/act}commodity/{http://www.gnucash.org/XML/cmdty}id"
            )
        accountdict[guid] = gb.Account(
            name=name, description=description, guid=guid, parent=parent, actype=actype, commodity=commodity
        )
    for acc_key, account in accountdict.items():
        if account.actype == "ROOT":
            account.name_full = ""
        else:
            ancestor = [account, accountdict[account.parent]]
            while len(ancestor) > 1:
                ances = ancestor[-1]
                curr = ancestor[-2]
                if ances.actype == "ROOT":
                    curr.name_full = curr.name
                    ancestor.pop()
                elif ances.name_full is not None:
                    curr.name_full = ances.name_full + ":" + curr.name
                    ancestor.pop()
                else:
                    ancestor.append(accountdict[ances.parent])
    for transaction in book.findall("./{http://www.gnucash.org/XML/gnc}transaction"):
        datestr = gb.getElementText(
            transaction, "./{http://www.gnucash.org/XML/trn}date-posted/{http://www.gnucash.org/XML/ts}date"
        )
        dt = datetime.datetime.strptime(datestr, "%Y-%m-%d %H:%M:%S %z").replace(tzinfo=None)
        if dt >= dtfrom and dt <= dtto:
            i = i + 1
        else:
            if dt < dtfrom:
                for split in transaction.findall(
                    "{http://www.gnucash.org/XML/trn}splits/{http://www.gnucash.org/XML/trn}split"
                ):
                    quantity = gb.getElementText(split, "{http://www.gnucash.org/XML/split}quantity")
                    account = accountdict[gb.getElementText(split, "{http://www.gnucash.org/XML/split}account")]
                    num, denom = quantity.split("/")
                    account.balance = account.balance + decimal.Decimal(num) / decimal.Decimal(denom)
            book.remove(transaction)
    for count in book.findall("{http://www.gnucash.org/XML/gnc}count-data"):
        if count.get("{http://www.gnucash.org/XML/cd}type") == "transaction":
            count.text = str(i)
    balancedict = defaultdict(list)
    for acc_key, account in accountdict.items():
        if (
            account.actype != "ROOT"
            and account.actype != "INCOME"
            and account.actype != "EXPENSE"
            and account.actype != "EQUITY"
            and account.balance != 0
        ):
            balancedict[account.commodity].append(account)
    for cmdy_key in balancedict:
        f = open(args.year + cmdy_key + ".qif", "w", encoding="utf-8")
        print("!Account", file=f)
        print("NEquity:Opening Balances:" + cmdy_key, file=f)
        print("TOth A", file=f)
        print("^", file=f)
        print("!Type:Oth A", file=f)
        print("D" + args.year + "-01-01", file=f)
        for account in balancedict[cmdy_key]:
            print("S" + account.name_full, file=f)
            print("$" + str(-account.balance), file=f)
        print("^", file=f)
        f.close()
xmltree.write(args.output, encoding="utf8")
