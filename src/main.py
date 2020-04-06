from process import Optimise
from api import API

if __name__ == '__main__':
    api = API('731b7c448f4f41fdaaef9d95284d7242')
    manifest = api.manifestUpdate('en')
    print(manifest)
    opt = Optimise('731b7c448f4f41fdaaef9d95284d7242', manifest)
    #opt.OptimiseBounties('Fuxticks')
    data = opt.getValueFromTable('432848324', 'DestinyInventoryItemDefinition')
    print(data)