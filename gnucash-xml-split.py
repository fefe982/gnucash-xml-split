import argparse
import decimal
import gzip
import datetime
from xml.etree import ElementTree

parser = argparse.ArgumentParser(description='GnuCash XML Splitter')
parser.add_argument('-i','--input', help='input file name',required=True)
parser.add_argument('-o','--output',help='output file name', required=True)
parser.add_argument('-y','--year', help='year of the transations to extract', required=True)
args = parser.parse_args()
 
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
    for transaction in book.findall('./{http://www.gnucash.org/XML/gnc}transaction'):
        datestr = transaction.find('./{http://www.gnucash.org/XML/trn}date-posted/{http://www.gnucash.org/XML/ts}date').text
        dt = datetime.datetime.strptime(datestr, '%Y-%m-%d %H:%M:%S %z').replace(tzinfo=None)
        if (dt >= dtfrom and dt <= dtto):
            i = i + 1
        else:
            #i = i + 1
            book.remove(transaction)
    for count in book.findall('{http://www.gnucash.org/XML/gnc}count-data'):
        if count.get('{http://www.gnucash.org/XML/cd}type') == 'transaction':
            count.text = str(i);

xmltree.write(args.output, encoding="utf8")
print(i);
