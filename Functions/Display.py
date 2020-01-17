import gui as Tkinter
from gui import *
import urllib.parse
from PIL import Image, ImageTk
import requests
import random
from io import BytesIO
import webbrowser
#from ttk import *
import time
import os

DisplayDataPosition = str(os.path.dirname(os.path.dirname(__file__))) + '/DataBase/DisplayData.txt'
import json
with open(DisplayDataPosition, 'r') as in_file:
    TestImageURL = json.load(in_file)
#TestImageURL = [['Ghost in the Shell (DVD, 1998, Original Japanese Dubbed and Subtitled English)', '0780063552929', '1.25', 7.25, 'https://i.ebayimg.com/00/s/MTYwMFgxMjAw/z/7AcAAOSwqp5eC3bc/$_3.JPG', 'https://www.ebay.com/itm/Ghost-Shell-DVD-1998-Original-Japanese-Dubbed-and-Subtitled-English-/312920734188', [['https://www.ebay.com/itm/Ghost-Shell-DVD-1998-Original-/164016988118', 'https://i.ebayimg.com/00/s/MTYwMFgxMjAw/z/gGAAAOSwYKBeD42b/$_3.JPG', '☆ Ghost in the Shell (DVD, 1998, Original ) ☆ ', '11.55']]]]

CurrentViewing = 0

# MainWindow = Tk()
# MainWindow.state("zoomed")
# app = Window(MainWindow)
ImageWidgets = []
global MainWindow

class VerticalScrolledFrame(Frame):
    """A pure Tkinter scrollable frame that actually works!
    * Use the 'interior' attribute to place widgets inside the scrollable frame
    * Construct and pack/place/grid normally
    * This frame only allows vertical scrolling

    """
    def __init__(self, parent, *args, **kw):

        InverseSensitivity = 60

        Frame.__init__(self, parent, *args, **kw)

        keys = {}
        if('height' in kw.keys()):
            height = kw['height']
            keys['height']=height
        if('width' in kw.keys()):
            width = kw['width']
            keys['width']=width

        # create a canvas object and a vertical scrollbar for scrolling it
        vscrollbar = Scrollbar(self, orient=VERTICAL)
        vscrollbar.pack(fill=Y, side=RIGHT, expand=FALSE)
        canvas = Canvas(self, bd=0, highlightthickness=0,
                        yscrollcommand=vscrollbar.set,**keys)
        canvas.pack(side=LEFT, fill=BOTH, expand=TRUE)
        vscrollbar.config(command=canvas.yview)



        # reset the view
        canvas.xview_moveto(0)
        canvas.yview_moveto(0)

        # create a frame inside the canvas which will be scrolled with it
        #print("hi")
        #print(**kw)
        self.interior = interior = Frame(canvas,**keys)
        interior_id = canvas.create_window(0, 0, window=interior,
                                           anchor=NW)

        # track changes to the canvas and frame width and sync them,
        # also updating the scrollbar
        def _configure_interior(event):
            # update the scrollbars to match the size of the inner frame
            size = (interior.winfo_reqwidth(), interior.winfo_reqheight())
            canvas.config(scrollregion="0 0 %s %s" % size)
            if interior.winfo_reqwidth() != canvas.winfo_width():
                # update the canvas's width to fit the inner frame
                canvas.config(width=interior.winfo_reqwidth())
        interior.bind('<Configure>', _configure_interior)

        def _configure_canvas(event):
            if interior.winfo_reqwidth() != canvas.winfo_width():
                # update the inner frame's width to fill the canvas
                canvas.itemconfigure(interior_id, width=canvas.winfo_width())
        canvas.bind('<Configure>', _configure_canvas)



        def _bound_to_mousewheel(event):
            canvas.bind_all("<MouseWheel>", _on_mousewheel)
            #print("MouseWheel1")

        def _unbound_to_mousewheel(event):
            canvas.unbind_all("<MouseWheel>")
            #print("MouseWheel2")

        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / InverseSensitivity)), "units")
            #print("MouseWheel3")

        canvas.bind('<Enter>', _bound_to_mousewheel)
        canvas.bind('<Leave>', _unbound_to_mousewheel)

def OpenInBrowzer(URL):
    webbrowser.open_new(URL)

def PackText(Text,X,Y):
    global MainWindow
    var = StringVar()
    text = Label(MainWindow, textvariable=var,wraplength=500)
    text.config(font=("Comic Sans MS", 15))
    text.config()
    var.set(Text)

    ImageWidgets.append(text)
    text.place(x=X, y=Y)

PhotoCacheDirectory = str(os.path.dirname(os.path.dirname(__file__))) + '/DataBase/ImageCache'
def GetImageData(ImageURL,MaxHeight=700,MaxWidth=500):
    # print(ImageURL)


    ChacheURL = ImageURL[0:len(ImageURL)]
    ChacheURL = ChacheURL.replace("/","").replace(":",'')
    # print("Cache URL " + str(ChacheURL.replace("/","").replace(":",'')))

    if(os.path.exists(PhotoCacheDirectory + '/' + ChacheURL)):
        # print('hi')
        try:
            image = Image.open(PhotoCacheDirectory + '/' + ChacheURL)
        except:
            return None
        save = 0
        #return image
    else:
        response = requests.get(ImageURL)
        image = Image.open(BytesIO(response.content))
        save = 1

    width, height = image.size

    NewWidthAtMaxHeight = int((MaxHeight / height) * width)
    NewHeightAtMaxWidth = int((MaxWidth / width) * height)
    if (NewWidthAtMaxHeight < MaxWidth):
        NewWidth = NewWidthAtMaxHeight
        NewHeight = MaxHeight
    else:
        NewHeight = NewHeightAtMaxWidth
        NewWidth = MaxWidth

    # Resize image
    image = image.resize((NewWidth, NewHeight), Image.BICUBIC)
    # print(ChacheURL)
    if(save == 1):
        image.save(PhotoCacheDirectory + "/" + str(ChacheURL))

    return image

def PackImage(ImageURL,X,Y,MaxWidth=500,MaxHeight=700):

    image = GetImageData(ImageURL,MaxHeight,MaxWidth)

    if(image == None):
        return None

    render = ImageTk.PhotoImage(image)
    img = Label(image=render)
    img.image = render
    global ImageWidgets

    # Create Image Widget
    ImageWidgets.append(img)
    img.place(x=X, y=Y)

def myfunction(event,canvas):
    canvas.configure(scrollregion=canvas.bbox("all"),width=200,height=200)

global MaxCount
MaxCount = 0

def PackImageFromURL(Input): #Input is [Name,SearchName,Price,AvgPrice,ImageURL,PageURL,[[SearchURL1,SearchImage1,Name1,Price1],[SearchURL2,SearchImage2,Name2,Price2],...]]

    ItemName = Input[0]
    SearchName = Input[1]
    Price = Input[2]
    AvgPrice = Input[3]
    ImageURL = Input[4]
    PageURL = Input[5]
    CompareAuctions = Input[6]


    #Define Max Image Dimentions
    MaxWidth = 500
    MaxHeight = 700

    # print(ImageURL)
    PackImage(ImageURL, 10, 150, MaxWidth, MaxHeight)

    def SimplifyString(Input):
        return Input.encode('ascii', 'ignore').decode('ascii')

    #Titles
    try:
        PackText(SimplifyString(ItemName),10,25)
        PackText(SimplifyString(SearchName),10,85)
        PackText(Price,MaxWidth, 25)
        PackText(AvgPrice,MaxWidth, 55)
    except:
        print([ItemName,SearchName,Price,AvgPrice])
        #quit()
        pass

    global MaxCount
    CurrentPosition = CurrentViewing%MaxCount
    PackText(str(CurrentPosition+1) + "/" + str(MaxCount),300,115)

    #Hyperlink
    link1 = Label(MainWindow, text="Google Hyperlink", fg="blue", cursor="hand2")
    link1.config(font=("Comic Sans MS", 15))
    link1.place(x=10,y=115)
    link1.bind("<Button-1>", lambda e: OpenInBrowzer(PageURL))

    frame1 = VerticalScrolledFrame(MainWindow,height=750,width=500, bd=2, relief=SUNKEN)
    frame1.place(x=600,y=50)
    ImageWidgets.append(frame1)

    def Pack(Text):
        var = StringVar()
        text = Label(frame1.interior, textvariable=var)
        text.config(font=("Comic Sans MS", 15))
        text.config()
        var.set(Text)

        ImageWidgets.append(text)

        text.pack()

    Links = []

    def AddLinkToText(PositionInLinks,URL):
        Links[PositionInLinks].bind("<Button-1>", lambda e: OpenInBrowzer(URL))

    p=0
    rowCount = 5
    for i in CompareAuctions:
        # print(i)
        if(i[1]!=""):
            ImageData = GetImageData(i[1], 500, 500)

            if ImageData == None: pass

            render = ImageTk.PhotoImage(ImageData)
            img = Label(frame1.interior,image=render)
            img.image = render

            # Create Image Widget
            ImageWidgets.append(img)
            img.grid(row=p*rowCount, column=0,rowspan=5)

        WrapLength = 400
        link1 = Label(frame1.interior, text=SimplifyString(str(i[2])), fg="blue", cursor="hand2",wraplength=WrapLength)
        link1.config(font=("Comic Sans MS", 15))
        ImageWidgets.append(link1)
        link1.grid(row=p*rowCount, column=1)
        Links.append(link1)
        #link1.bind("<Button-1>", lambda e: hi(i[0]))
        AddLinkToText(p,i[0])

        link1 = Label(frame1.interior, text=str(i[3]), wraplength=WrapLength)
        link1.config(font=("Comic Sans MS", 15))
        link1.grid(row=p * rowCount+1, column=1)


        p = p + 1



def PackNextImage():
    global MainWindow
    # print('Packing Next Image')
    global CurrentViewing
    CurrentViewing = CurrentViewing + 1
    global ImageWidgets
    # print(ImageWidgets)
    for i in ImageWidgets:
        i.destroy()
    ImageWidgets = []
    global Length
    global Input
    PackImageFromURL(Input[CurrentViewing%Length])
    # print(MainWindow.children)
    # print(CurrentViewing)

def PackLastImage():
    global MainWindow
    # print("Packing Last Image")
    global CurrentViewing
    CurrentViewing = CurrentViewing - 1
    if(CurrentViewing < 0):
        global Length
        CurrentViewing = Length-1
    global ImageWidgets
    # print(ImageWidgets)
    for i in ImageWidgets:
        i.destroy()
    ImageWidgets = []
    global Input
    PackImageFromURL(Input[CurrentViewing%Length])
    # print(MainWindow.children)
    # print(CurrentViewing)

from tinydb import TinyDB
AvgPriceDataBase1 = TinyDB(os.path.dirname(os.path.dirname(__file__)) + "/DataBase/LinkToAvgPrice")
ErrorsDataBase1 = TinyDB(os.path.dirname(os.path.dirname(__file__)) + "/Logs/Errors")
UPCDataBase1 = TinyDB(os.path.dirname(os.path.dirname(__file__)) + "/DataBase/LinkToUPC")

import Get
def Search(Title):
    Prices, FinalSearchName, SearchedItems = Get.AvgPrice(None,Title,0,0,Title,0,AvgPriceDataBase1,ErrorsDataBase1,UPCDataBase1)

    frame1 = VerticalScrolledFrame(MainWindow, height=750, width=500, bd=2, relief=SUNKEN)
    frame1.place(x=600, y=50)
    ImageWidgets.append(frame1)

    Links = []
    def AddLinkToText(PositionInLinks,URL):
        Links[PositionInLinks].bind("<Button-1>", lambda e: OpenInBrowzer(URL))

    p = 0
    rowCount = 5

    Images = []
    for i in SearchedItems:
        Images.append(i[1])

    LoadImages(Images)

    for i in SearchedItems:
        # print(i)
        if (i[1] != ""):
            ImageData = GetImageData(i[1], 500, 500)

            if ImageData == None: pass

            render = ImageTk.PhotoImage(ImageData)
            img = Label(frame1.interior, image=render)
            img.image = render

            # Create Image Widget
            ImageWidgets.append(img)
            img.grid(row=p * rowCount, column=0, rowspan=5)

        WrapLength = 400
        link1 = Label(frame1.interior, text=str(i[2]), fg="blue", cursor="hand2", wraplength=WrapLength)
        link1.config(font=("Comic Sans MS", 15))
        ImageWidgets.append(link1)
        link1.grid(row=p * rowCount, column=1)
        Links.append(link1)
        # link1.bind("<Button-1>", lambda e: hi(i[0]))
        AddLinkToText(p, i[0])

        link1 = Label(frame1.interior, text=str(i[3]), wraplength=WrapLength)
        link1.config(font=("Comic Sans MS", 15))
        link1.grid(row=p * rowCount + 1, column=1)

        p = p + 1

def Statup(InputSet):
    global MaxCount
    MaxCount = len(InputSet)

    #InputSet.sort()
    InputSet = sorted(InputSet, key=lambda x: float(x[2]))

    PreloadImages(InputSet)

    global MainWindow
    MainWindow = Tk()
    MainWindow.state("zoomed")
    app = Window(MainWindow)

    global Length
    Length = len(InputSet)

    global Input
    Input = InputSet

    quitButton = Button(text="Next",command=PackNextImage)
    quitButton.place(x=0,y=0)

    quitButton = Button(text="Back",command=PackLastImage)
    quitButton.place(x=50,y=0)

    TextBox = Text(height=2, width=30)
    TextBox.place(x=600,y=0)

    TextBoxSearchButton = Button(text="Search",command=lambda: Search(TextBox.get("1.0",'end-1c')))
    TextBoxSearchButton.place(x=850,y=0)

    SkipTextBox = Text(height=2, width=6)
    SkipTextBox.place(x=950, y=0)

    def SkipTo(Number):
        global CurrentViewing
        CurrentViewing = int(Number)
        PackLastImage()

    SkipTextBoxSearchButton = Button(text="Move", command=lambda: SkipTo(SkipTextBox.get("1.0", 'end-1c')))
    SkipTextBoxSearchButton.place(x=1000, y=0)

    global ImageWidgets
    ImageWidgets = []

    PackImageFromURL(InputSet[CurrentViewing % len(InputSet)])

    MainWindow.mainloop()

def PreloadImages(InputSet):
    ImageURLs = []
    for Item in InputSet:
        #Preload 4
        #print("Item" + str(Item))
        for i in range(10):
            try:
                ImageURLs.append(Item[4])
                for Item2 in Item[6]:
                    #Preload 1
                    # print("Item2" + str(Item2))
                    ImageURLs.append(Item2[1])
                break
            except:
                pass

    print('loaded')
    LoadImages(ImageURLs,16)

def GetMultiImageData(MultiImageArray):
    for i in MultiImageArray:
        GetImageData(i)
        print('get: ' + str(i))

        #print(i)

def LoadImages(ImageURLsArray,ThreadCount=16):
    import multiprocessing
    import concurrent.futures
    from more_itertools import grouper

    executor = concurrent.futures.ThreadPoolExecutor(ThreadCount)
    ItemsPerGroup = 3#int(len(ImageURLsArray)/ThreadCount)
    futures = [executor.submit(GetMultiImageData, group)for group in grouper(ItemsPerGroup, ImageURLsArray)]
    concurrent.futures.wait(futures)



#Statup(TestImageURL)
#PreloadImages(TestImageURL)
#Search("dvd neon genesis evangelion")