import webapp2
from google.appengine.api import users


import jinja2
import csv
import os
import StringIO

from transaction import Transaction

jinja_environment = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))


class UploadPage(webapp2.RequestHandler):
    
    mintColumnToAttribute = {
     "Date": 'transactionDate', 
     "Description": 'description', 
     "Original Description": 'originalDescription', 
     "Amount": 'amount', 
     "Transaction Type": 'transactionType', 
     "Category": 'transactionCategory', 
     "Account Name": 'accountName',
     "Labels": 'labels', 
     "Notes": 'notes'
    }
    
    def get(self):
        user = users.get_current_user()

        if user:            
            template = jinja_environment.get_template('upload.html')
            self.response.out.write(template.render(users=users))
            
            
        else:
            self.redirect(users.create_login_url(self.request.uri))


    def post(self):
        user = users.get_current_user()

        if user:
            transactionsFile = self.request.get('transactions')
            
            transactionsReader = csv.reader(StringIO.StringIO(transactionsFile))
            
            header = transactionsReader.next()
            
            transactions = []
            
            for row in transactionsReader:
                values = {}
                
                for i in range(len(row)):
                    attribute = self.mintColumnToAttribute[header[i]]
                    values[attribute] = row[i]
                    
                t = Transaction.from_mint_transaction(**values)
                t.userid = user.user_id()
                
                transactions.append(t)
            
            template = jinja_environment.get_template('dump.html')
            self.response.out.write(template.render(users=users, transactions=transactions))
        else:
            self.redirect(users.create_login_url(self.request.uri))


app = webapp2.WSGIApplication([('/upload', UploadPage)], debug=True)

