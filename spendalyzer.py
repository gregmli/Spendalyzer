import webapp2
from google.appengine.api import users
from google.appengine.ext import db



import jinja2
import csv
import os
import StringIO
import urllib

from transaction import Transaction
from budget import CategoryMapManager, BudgetGroup, calculate

jinja_environment = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))

def urlencode_filter(s):
    if type(s) == 'Markup':
        s = s.unescape()
    s = s.encode('utf8')
    s = urllib.quote_plus(s)
    return jinja2.Markup(s)

jinja_environment.filters['urlencode'] = urlencode_filter

class UploadPage(webapp2.RequestHandler):
    
    mintColumnToAttribute = {
     "Date": 'transactionDate', 
     "Description": 'description', 
     "Original Description": 'originalDescription', 
     "Amount": 'amount', 
     "Transaction Type": 'transactionType', 
     "Category": 'category', 
     "Account Name": 'accountName',
     "Labels": 'labels', 
     "Notes": 'notes'
    }
    
    def get(self):
        user = users.get_current_user()

        if user is None:            
            self.redirect(users.create_login_url(self.request.uri))
           
        else:
            template = jinja_environment.get_template('upload.html')
            self.response.out.write(template.render(users=users))
            
 

    def post(self):
        user = users.get_current_user()

        if user is None:
            self.redirect(users.create_login_url(self.request.uri))
        
        else:
            transactionsFile = self.request.get('transactions')
            
            transactionsReader = csv.reader(StringIO.StringIO(transactionsFile))
            
            header = transactionsReader.next()
            
            for row in transactionsReader:
                values = {}
                
                for i in range(len(row)):
                    attribute = self.mintColumnToAttribute[header[i]]
                    values[attribute] = row[i]
                    
                t = Transaction.importMintTransaction(userid = user.user_id(), **values)
                
                t.put()
                
            self.redirect("/transactions")
            

class AnalyzePage(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()

        if user is None:
            self.redirect(users.create_login_url(self.request.uri))
        
        else:
            q = db.GqlQuery("SELECT * FROM Transaction " +
                            "WHERE userid = :1 " + 
                            "ORDER BY transactionDate DESC ", 
                            user.user_id())
            
            transactionsIt = q.run()
            
            transactions = []
            for t in transactionsIt:
                transactions.append(t)
            
            allCategories = CategoryMapManager.getCategoriesFromTransactions(transactions)
            
            mapManager = CategoryMapManager(user, allCategories)
            categoryGroupMap = mapManager.getMapping()
            
            prefs_k = db.Key.from_path('UserBudgetPreferences', user.user_id())
            prefs = db.get(prefs_k)
            
            budgetResult = calculate(transactions, categoryGroupMap, prefs)
            
            template = jinja_environment.get_template('analyze.html')
            self.response.out.write(template.render(users=users, result=budgetResult))

class ConfigureCategoriesPage(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()

        if user is None:
            self.redirect(users.create_login_url(self.request.uri))
        
        else:
            q = Transaction.all()
            q.filter("userid =", user.user_id())
                
            transactions = q.run()
            
            allCategories = CategoryMapManager.getCategoriesFromTransactions(transactions)
            mapManager = CategoryMapManager(user, allCategories)
            groupMap = dict()
            for grp in BudgetGroup.getAllGroups():
                groupMap[grp] = mapManager.getCategories(grp)
            
            template = jinja_environment.get_template('categories.html')
            self.response.out.write(template.render(users=users, groupMap=groupMap))
        
    def post(self):
        user = users.get_current_user()

        if user is None:
            self.redirect(users.create_login_url(self.request.uri))
            
        else:
            mapManager = CategoryMapManager(user)
            args = self.request.arguments()
            
            for arg in args:
                mapManager.setMapping(arg, self.request.get(arg))
            
            mapManager.writeMappings()
            self.redirect("/categories")
        
            
class TransactionsPage(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()

        if user is None:
            self.redirect(users.create_login_url(self.request.uri))
        
        else:
            category = self.request.get("category")
            
            q = Transaction.all()
            q.filter("userid = ", user.user_id())
            q.order("-transactionDate")
            
            if (category):
                q.filter("transactionCategory = ", category)
            
            template = jinja_environment.get_template('transactions.html')
            self.response.out.write(template.render(users=users, transactions=q.run()))


class AdminPage(webapp2.RequestHandler):
        
    def get(self):
        user = users.get_current_user()
        
        if user and users.is_current_user_admin():
            success  = self.request.get('success')
            error = self.request.get('error')
            
            template = jinja_environment.get_template('admin.html')
            self.response.out.write(template.render(users=users, success=success, error=error))

        else:
            self.redirect(users.create_login_url(self.request.uri))
            


    def post(self):
        user = users.get_current_user()

        if user is None:
            self.redirect(users.create_login_url(self.request.uri))
        
        else:
            action = self.request.get('action')
            
            success = None
            error = None
            
            if action == 'clearUser':
                q = Transaction.all()
                q.filter("userid =", user.user_id())
                
                try:
                    for t in q.run():
                        t.delete()
                        
                except db.NotSavedError:
                    error = "Couldn't delete user's transactions because of a NotSavedError"
                    
                else:
                    
                    try:
                        mapManager = CategoryMapManager(user)
                        mapManager.clearMappings()
                            
                    except db.NotSavedError:
                        error = "Couldn't delete user's category mappings because of a NotSavedError"
                        
                    else:
                        success = "Removed all records for " + user.nickname()

            else:
                error = 'Invalid action: "' + action + '"'
            
            params = {}
            if success:
                params['success'] = success
            if error:
                params['error'] = error
                
            params = urllib.urlencode(params)
            self.redirect('/admin?' + params)
                
            
            

app = webapp2.WSGIApplication([('/upload', UploadPage),
                               ('/transactions', TransactionsPage),
                               ('/categories', ConfigureCategoriesPage),
                               ('/admin', AdminPage),
                               ('/analyze', AnalyzePage)], 
                              debug=True)

