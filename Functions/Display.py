from gui import *
from PIL import Image, ImageTk
import requests
from io import BytesIO
import webbrowser
import os
import json
import Get
# from tinydb import TinyDB

########################################################################################################################
# Display.py
#
# Display covers all Tkninter based operations, command Startup generates main window and starts necessary systems
#
# VerticalScrolledFrame is a custom class to make a scrollable frame for images
# OpenInBrowzer("URL") opens a webpage in the default browser
# PackText("Text",(int)X,(int)Y) places text in a position in the default Tk window
# GetImageData("ImageURL",(int)MaxHeight,(int)MaxWidth) returns the data for an image from the address that fits within
# the bounds
# PackImage("ImageURL",(int)X,(int)Y,(int)MaxWidth,(int)MaxHeight) places an image at the position in the main window
# SimplifyString("Str") returns an ascii only version of the input string
# PackImageFromURL("Input") Places text, main display image, and comparison items in the main window
# PackNextImage() Switches from the currently viewed item to the next item to be viewed
# PackLastImage() Switches from the currently viewed item to the previously viewed item
# Search("SearchText") Searches ebay for items matching SearchText and adds the found items to the scrollable frame
# Startup(InputSet) Initializes the Tk window and begins placing objects
# PreloadImages(InputSet) Preload the images from urls in Input Set, (MultiThreaded)
# GetMultiImageData(["ImageURLArray"]) Preload image data for urls in Image URL Array, called by LoadImages()
# LoadImages(["ImageURLArray"],(int)ThreadCount) Preload image data from ImageURL Array using multiple threads
#
# Input Set Example:
# InputSet = [['Title', 'UPC', 'Price', AvgPrice, 'ImageURL', 'PageURL',
#               [['ComparisonPage1', 'ComparisonImage1', 'ComparisonTitle1', 'ComparisonPrice1'],
#               ... ,
#               [['ComparisonPage100', 'ComparisonImage100', 'ComparisonTitle100', 'ComparisonPrice100']]]
#            ]]
#
########################################################################################################################

# Initialization

# If the Image Cache directory dosen't exist then create it
PhotoCacheDirectory = str(os.path.dirname(os.path.dirname(__file__))) + '/DataBase/ImageCache'
if not os.path.exists(PhotoCacheDirectory):
    os.makedirs(PhotoCacheDirectory)

# Grab position of display data file
# All data that is used to display things is stored in the display data file
# Currently this is only used to display data from the last run if the Tkinter window is closed
DisplayDataPosition = str(os.path.dirname(os.path.dirname(__file__))) + '/DataBase/DisplayData.txt'
try:
    with open(DisplayDataPosition, 'r') as in_file: #Place display data into TestImageURL
        TestImageURL = json.load(in_file)
except:
    pass

CurrentViewing = 0  # Currently viewing is the current object position that is being displayed in Display Data
ImageWidgets = []
global MainWindow

# Data bases that are used for cached searches
# AvgPriceDataBase1 = TinyDB(os.path.dirname(os.path.dirname(__file__)) + "/DataBase/LinkToAvgPrice")
# ErrorsDataBase1 = TinyDB(os.path.dirname(os.path.dirname(__file__)) + "/Logs/Errors")
# UPCDataBase1 = TinyDB(os.path.dirname(os.path.dirname(__file__)) + "/DataBase/LinkToUPC")

MaxCount = 0  # Contains the total item pages that are displayed

# Vertically scrolled frame is a an edited version of VerticalScrolledFrame from online, if the mouse hovers over the
# frame then you can use the scroll wheel to scroll.
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


        #Scroll wheel events
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


# Open In Browzer opens the URL in the default web browser on the system
def OpenInBrowzer(URL):
    webbrowser.open_new(URL)


# Pack Text places text at a given position in the Tkinter window
def PackText(Text,X,Y):
    global MainWindow
    var = StringVar()
    text = Label(MainWindow, textvariable=var,wraplength=500)
    text.config(font=("Comic Sans MS", 15))
    text.config()
    var.set(Text)

    #append text object to image widgets so it can be deleted when displaying the next item
    ImageWidgets.append(text)
    text.place(x=X, y=Y)


# Get Image data checks to see if the image is stored locally, if it is not then it grabs it from the internet
#  and stores it locally.
#
#  Potential Improvements: cache a list of all images instead of checking each time.
#  Other: Maby save image at full scale or some larger scale so that if a low res image is requested once and then
#         a high res is requested the high res is not the low res upscaled.
ImageCache = {}
def GetImageData(ImageURL,MaxHeight=700,MaxWidth=500):

    ChacheURL = ImageURL[0:len(ImageURL)] #duplicate ImageURL string

    #Local version replaces /'s with :'s so http://photo.jpg is stored as http:::photo.jpg
    ChacheURL = ChacheURL.replace("/","").replace(":",'')

    if(ChacheURL in ImageCache):
        image = ImageCache[ChacheURL]
        save = 0
    #Check if photo is stored locally
    elif(os.path.exists(PhotoCacheDirectory + '/' + ChacheURL)):
        #If photo is stored locally load photo into image
        try:
            image = Image.open(PhotoCacheDirectory + '/' + ChacheURL)
        except:
            return None # if inable to load photo return None (Error State)
        save = 0 # Save is used to determine if the photo should be saved later (0 is Already saved)

    else:
        response = requests.get(ImageURL) # Grab image from URL
        image = Image.open(BytesIO(response.content))
        save = 1 # Mark save as 1 (Still needs to be saved)

    width, height = image.size # Grab height and width of current image

    # Determines what dimentions the image needs to be shrunk to to fit within the MaxHeight and MaxWidth dimensions
    NewWidthAtMaxHeight = int((MaxHeight / height) * width) # Calculate the width of the image if it is at max height
    NewHeightAtMaxWidth = int((MaxWidth / width) * height) # Calculate the height of the image if it is at max width
    if (NewWidthAtMaxHeight < MaxWidth): #If the image at the max height is thinner than the max width then the height
                                         # is the limiting dimention
        NewWidth = NewWidthAtMaxHeight
        NewHeight = MaxHeight
    else: # If the height is not the limiting dimention then the width is
        NewHeight = NewHeightAtMaxWidth
        NewWidth = MaxWidth

    # Resize image to match with new dimensions
    image = image.resize((NewWidth, NewHeight), Image.BICUBIC)

    if(save == 1): # If save was set earlier then save the image
        image.save(PhotoCacheDirectory + "/" + str(ChacheURL))

    ImageCache[ChacheURL] = image
    return image


# Pack Image adds an image to the main window at the position X,Y with max dimentions (one of the two will end up smaller)
def PackImage(ImageURL,X,Y,MaxWidth=500,MaxHeight=700):

    image = GetImageData(ImageURL,MaxHeight,MaxWidth) #Gets image from cache/web

    if(image == None): #if inable to get image exit with an Error
        return None

    render = ImageTk.PhotoImage(image) #Setup image in Tk
    img = Label(image=render)
    img.image = render
    img.place(x=X, y=Y)

    global ImageWidgets
    ImageWidgets.append(img) # Add image to list so it can be removed when moving onto next object


# Simplify String removes all non ascii characters since Tkinter is unable to display these
def SimplifyString(Input):
    return Input.encode('ascii', 'ignore').decode('ascii')


# Pack Image From URL places all of the images, text and links that are seen in the main tk window.
def PackImageFromURL(Input):

    # Grab image data from input is formated as such:
    # [Name,SearchName,Price,AvgPrice,ImageURL,PageURL,[[SearchURL1,SearchImage1,Name1,Price1],[SearchURL2,SearchImage2,Name2,Price2],...]]
    ItemName = Input[0]
    SearchName = Input[1]
    Price = Input[2]
    AvgPrice = Input[3]
    ImageURL = Input[4]
    PageURL = Input[5]
    CompareAuctions = Input[6]

    # Define Max Image Dimentions
    MaxWidth = 500
    MaxHeight = 700

    # Place main big image on the left side
    PackImage(ImageURL, 10, 150, MaxWidth, MaxHeight)

    # Place text for Name, SearchName, Price and Avg Price for main object
    try:
        PackText(SimplifyString(ItemName),10,25)
        PackText(SimplifyString(SearchName),10,85)
        PackText(Price,MaxWidth, 25)
        PackText(AvgPrice,MaxWidth, 55)
    except:
        print([ItemName,SearchName,Price,AvgPrice]) # If failed to place title then print out title data
        pass

    global MaxCount
    CurrentPosition = CurrentViewing%MaxCount # Wraps the Current viewing variable between 0 and MaxCount - 1
    PackText(str(CurrentPosition+1) + "/" + str(MaxCount),300,115) # Place text for current position

    # Generate and place hyperlink
    link1 = Label(MainWindow, text="Google Hyperlink", fg="blue", cursor="hand2")
    link1.config(font=("Comic Sans MS", 15))
    link1.place(x=10,y=115)
    link1.bind("<Button-1>", lambda e: OpenInBrowzer(PageURL))

    # Add scrollable frame to the right side
    ScrollFramePosition = [ScreenSize[0] / 2 - 20, ScreenSize[1] - 100, ScreenSize[0] / 2 + 10, 50]  # Width,Height,X,Y
    frame1 = VerticalScrolledFrame(MainWindow, height=ScrollFramePosition[1], width=ScrollFramePosition[0], bd=2,
                                   relief=SUNKEN)
    frame1.place(x=ScrollFramePosition[2], y=ScrollFramePosition[3])
    ImageWidgets.append(frame1)

    Links = []

    # Add Link to Text binds the on click open browser thing to the input text
    def AddLinkToText(PositionInLinks,URL):
        Links[PositionInLinks].bind("<Button-1>", lambda e: OpenInBrowzer(URL))

    photorow=0  # Contains the current photo row
    rowCount = 5  # Contains text rows per photo row
    for i in CompareAuctions:

        if(i[1]!=""):  # If an image link is given then place image
            ImageData = GetImageData(i[1], 500, 500) # Grab image data

            if ImageData == None: pass  # If unable to grab image data then skip placing image

            # Place image in scrolling frame
            render = ImageTk.PhotoImage(ImageData)
            img = Label(frame1.interior,image=render)
            img.image = render

            # Add image to Image Widget so it can be removed when switching to next image
            ImageWidgets.append(img)
            img.grid(row=photorow*rowCount, column=0,rowspan=5)


        WrapLength = 400  # Wrap length for text and links

        # Place link for image to right of image
        link1 = Label(frame1.interior, text=SimplifyString(str(i[2])), fg="blue", cursor="hand2",wraplength=WrapLength)
        link1.config(font=("Comic Sans MS", 15))
        ImageWidgets.append(link1)
        link1.grid(row=photorow*rowCount, column=1)
        Links.append(link1)
        AddLinkToText(photorow,i[0])

        # Place Text for image below link
        link1 = Label(frame1.interior, text=str(i[3]), wraplength=WrapLength)
        link1.config(font=("Comic Sans MS", 15))
        link1.grid(row=photorow * rowCount+1, column=1)

        photorow = photorow + 1  # Move to next image


# Pack Next Image is bound to the next button in the window and destroyed everything in the current window and loads
# the next window
def PackNextImage():
    global MainWindow
    global CurrentViewing
    CurrentViewing = CurrentViewing + 1 #Index of next window to load

    global ImageWidgets #Remove everything in current window
    for i in ImageWidgets:
        i.destroy()
    ImageWidgets = []

    global MaxCount #Load next window, wrapping Current Viewing to MaxCount (Number of Items in display list)
    global Input
    PackImageFromURL(Input[CurrentViewing%MaxCount])


# Pack Last Image is bound to the last button in the window and destroys everything in the current window and loads the
#  previous window
def PackLastImage():
    global MainWindow
    global CurrentViewing
    CurrentViewing = CurrentViewing - 1 # Index of last window

    if(CurrentViewing < 0): # If index is less than 0 wrap around to highest value (MaxCount - 1)
        global MaxCount
        CurrentViewing = MaxCount-1

    global ImageWidgets # Remove everything from current window
    for i in ImageWidgets:
        i.destroy()
    ImageWidgets = []

    global Input # Place new window
    PackImageFromURL(Input[CurrentViewing%MaxCount])


#Search is activated when pressing the search button and generates and places items that come up in search
def Search(Title):

    ScrollFramePosition = [ScreenSize[0]/2-20,ScreenSize[1]-100,ScreenSize[0]/2+10,50]# Width,Height,X,Y

    # Search from cached or web
    Prices, FinalSearchName, SearchedItems = Get.AvgPrice(None,Title,0,0,Title,0)

    FrameIndex = [str(a) for a in ImageWidgets]
    for ItemIndex in range(len(FrameIndex)):
        if('verticalscrolledframe' in FrameIndex[ItemIndex]):
            ImageWidgets[ItemIndex].destroy()

    # Place scrolled frame
    frame1 = VerticalScrolledFrame(MainWindow, height=ScrollFramePosition[1], width=ScrollFramePosition[0], bd=2, relief=SUNKEN)
    frame1.place(x=ScrollFramePosition[2], y=ScrollFramePosition[3])
    ImageWidgets.append(frame1)

    #Duplicate text from PackImageFromURL, Move to function
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
        link1 = Label(frame1.interior, text=SimplifyString(str(i[2])), fg="blue", cursor="hand2", wraplength=WrapLength)
        link1.config(font=("Comic Sans MS", 15))
        ImageWidgets.append(link1)
        link1.grid(row=p * rowCount, column=1)
        Links.append(link1)
        AddLinkToText(p, i[0])

        link1 = Label(frame1.interior, text=SimplifyString(str(i[3])), wraplength=WrapLength)
        link1.config(font=("Comic Sans MS", 15))
        link1.grid(row=p * rowCount + 1, column=1)

        p = p + 1

ScreenSize = [0,0]

# Startup generates main window
def Startup(InputSet):
    global MaxCount
    MaxCount = len(InputSet) # Max count is the number of items to display

    InputSet = sorted(InputSet, key=lambda x: float(x[2])) #Sort input set by price

    PreloadImages(InputSet) # Preloads images that are in input set

    # Opens new tk window
    global MainWindow
    MainWindow = Tk()
    MainWindow.state("zoomed")
    app = Window(MainWindow)

    # Define Input
    global Input
    Input = InputSet

    #Add buttons to widnow
    #Next button
    quitButton = Button(text="Next",command=PackNextImage)
    quitButton.place(x=0,y=0)

    #Back Button
    quitButton = Button(text="Back",command=PackLastImage)
    quitButton.place(x=50,y=0)

    #Text box for searching and search button, when button is pressed read text in box and call search on it to display
    #  search in scrolled window
    TextBox = Text(height=2, width=30)
    TextBox.place(x=600,y=0)
    TextBoxSearchButton = Button(text="Search",command=lambda: Search(TextBox.get("1.0",'end-1c')))
    TextBoxSearchButton.place(x=850,y=0)

    # Skip text box for skipping to different indicies
    SkipTextBox = Text(height=2, width=6)
    SkipTextBox.place(x=950, y=0)

    #Skip to function that jumps to indicies
    def SkipTo(Number):
        global CurrentViewing
        CurrentViewing = int(Number) # Number is one more than item you want to skip to
        PackLastImage() # Pack previous item so it packs number - 1

    #Place skip button that reads text box and calls skip to function on text inside
    SkipTextBoxSearchButton = Button(text="Move", command=lambda: SkipTo(SkipTextBox.get("1.0", 'end-1c')))
    SkipTextBoxSearchButton.place(x=1000, y=0)

    global ImageWidgets
    ImageWidgets = []

    #Initial pack image
    PackImageFromURL(InputSet[CurrentViewing % len(InputSet)])

    def on_resize(event):
        global ScreenSize
        ScreenSize[0] = MainWindow.winfo_width()
        ScreenSize[1] = MainWindow.winfo_height()
        #print(ScreenSize)

    MainWindow.bind("<Configure>", on_resize)

    PreviousEnter = None
    def EnterButtonPressed(d):
        print(d)
        if(PreviousEnter == "Search"):
            Search(TextBox.get("1.0", 'end-1c'))
            TextBox.delete("1.0", END)
        elif(PreviousEnter == "Skip"):
            SkipTo(SkipTextBox.get("1.0", 'end-1c'))
            SkipTextBox.delete("1.0", END)

    def SearchBoxEntered(d):
        print(d)
        nonlocal  PreviousEnter
        PreviousEnter = "Search"

    def SkipBoxEntered(d):
        print(d)
        nonlocal PreviousEnter
        PreviousEnter = "Skip"

    MainWindow.bind('<Return>', EnterButtonPressed)
    TextBox.bind("<Enter>",SearchBoxEntered)
    SkipTextBox.bind("<Enter>", SkipBoxEntered)

    # Startup Main Window
    MainWindow.mainloop()


#Pre load Images loads images into cache before thay are needed
def PreloadImages(InputSet):
    ImageURLs = []
    for Item in InputSet: # For every item
        ImageURLs.append(Item[4]) # load the main item image
        for Item2 in Item[6]:
            ImageURLs.append(Item2[1]) # and all of the comparison images

    print('loaded')
    LoadImages(ImageURLs,16) #Load images using 16 threads


def GetMultiImageData(MultiImageArray):
    # Preload images for all images in Multi Image Array
    for i in MultiImageArray:
        GetImageData(i)


def LoadImages(ImageURLsArray,ThreadCount=16):
    import concurrent.futures
    from more_itertools import grouper

    #Setup multithreaded for using the number of threads in ThreadCount
    executor = concurrent.futures.ThreadPoolExecutor(ThreadCount)
    ItemsPerGroup = 3 #Items per group is the number of items that each thread is given to load before it is given a new set of items
    futures = [executor.submit(GetMultiImageData, group)for group in grouper(ItemsPerGroup, ImageURLsArray)]
    #concurrent.futures.wait(futures)

def StartupLast():
    StartupThreaded(TestImageURL)

def StartupThreaded(InputSet):
    import threading

    class FuncThread(threading.Thread):
        def __init__(self, target, *args):
            self._targets = target
            self._argss = args
            threading.Thread.__init__(self)

        def run(self):
            self._targets(*self._argss)

    DisplayThread = FuncThread(Startup,InputSet)
    DisplayThread.start()

