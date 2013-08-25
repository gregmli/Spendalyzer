from google.appengine.ext import db


class BudgetGroup():
    INCOME = "Income"
    COMMITED = "Committed"
    IRREGULAR = "Irregular"
    FUN = "Fun"
#    RETIREMENT = "Retirement"
    SAVINGS = "Savings"
    UNGROUPED = "Ungrouped"
    IGNORED = "Ignored"
    
    @staticmethod
    def getAllGroups():
        return [BudgetGroup.INCOME, BudgetGroup.COMMITED, BudgetGroup.IRREGULAR, BudgetGroup.FUN, 
                BudgetGroup.SAVINGS, BudgetGroup.UNGROUPED, BudgetGroup.IGNORED]

class CategoryMapping(db.Model):
    transactionCategory = db.StringProperty()
    budgetGroup = db.StringProperty()
    
    
class UserBudgetPreferences(db.Model):
    userid = db.StringProperty()
    skipRetirement = db.BooleanProperty()
    

class CategoryMapManager():
    def __init__(self, user, allCategories = None):
        self.user = user
        self.categories = allCategories
        self.mapping = {}
        
        
    def clearMappings(self):
        q = CategoryMapping.all()
        parentKey = db.Key.from_path('User', self.user.user_id())
        q.ancestor(parentKey)
        
        for m in q.run():
            m.delete()
    
    def getMapping(self):
        if (len(self.mapping) == 0):
            
            #q = db.GqlQuery("SELECT * FROM CategoryMapping " +
            #                "WHERE userid = :1 ", 
            #                self.user.user_id())
            q = CategoryMapping.all()
            parentKey = db.Key.from_path('User', self.user.user_id())
            q.ancestor(parentKey)
            
            for m in q.run():
                self.mapping[m.transactionCategory] = m.budgetGroup
            
            if self.categories is not None:
                for c in self.categories:
                    if (c not in self.mapping):
                        self.mapping[c] = BudgetGroup.UNGROUPED
        
        return self.mapping
    

    def getCategories(self, budgetGroup):
        ret = []
        mapping = self.getMapping()
        for cat, grp in mapping.items():
            if grp==budgetGroup:
                ret.append(cat)
        return ret
    
    @staticmethod
    def getCategoriesFromTransactions(transactions):
        categories = set()
        
        for t in transactions:
            categories.add(t.transactionCategory)
            
            
        return categories
    
    
    def setMapping(self, transactionCategory, budgetGroup):
        self.mapping[transactionCategory] = budgetGroup
    
    
    def writeMappings(self):
        
        for c, g in self.mapping.items():
            key = db.Key.from_path('User', self.user.user_id(), 'CategoryMapping', c)
            cm = CategoryMapping(key=key, transactionCategory=c, budgetGroup=g)
            cm.put()
    
    

class BudgetResult():
    def __init__(self, categoryMap, userBudgetPreferences):
        self.cmap = categoryMap
        self.prefs = userBudgetPreferences
        self.groupCategoryMap = {}
        self.categoryTransactions = {}
        
        for c,g in self.cmap.items():
            
            if c not in self.categoryTransactions:
                self.categoryTransactions[c] = []
            
            if (g not in self.groupCategoryMap):
                self.groupCategoryMap[g] = set()
            
            self.groupCategoryMap[g].add(c)
            
            
    
    def addTransaction(self, t):
        transactions = self.categoryTransactions[t.transactionCategory]
        transactions.append(t)
        
    def getCategoryTotal(self, category):
        transactions = self.categoryTransactions[category]
        
        ret = 0.0
        for t in transactions:
            ret += t.getAmount()
        
        return ret
    
    def getGroups(self):
        # use this to effect a fixed display order
        allGroups = BudgetGroup.getAllGroups()
        
        actualGroups = self.groupCategoryMap.keys()
        
        groups = filter(lambda x: x in actualGroups and x != BudgetGroup.IGNORED, allGroups)
        
        return groups
    
    def getCategoriesInGroup(self, group):
        return self.groupCategoryMap[group]
        
    
    def getGroupTotal(self, group):
        ret = 0.0
        
        for c in self.getCategoriesInGroup(group):
            ret += self.getCategoryTotal(c)
                
        return ret
        
    
def calculate(transactions, categoryMap, userBudgetPreferences):
    result = BudgetResult(categoryMap, userBudgetPreferences)
    
    for t in transactions:
        result.addTransaction(t)
    
    
    return result
            
    
    
            
            
    
    
    