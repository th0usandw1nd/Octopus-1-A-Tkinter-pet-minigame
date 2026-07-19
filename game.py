from tkinter.ttk import *
from tkinter import *
from PIL import Image, ImageTk, ImageSequence
import json
from tkinter import ttk, messagebox
import random
import os
import sys
import shutil

"""
改為執行動作(出門?)扣值? done
工作加錢 done
體力值:出門或玩耍或訓練會消耗體力。 done
睡覺消耗心情值與飢餓值回體力，保底回5點 done
睡覺存檔，天數+1 done
訓練增加體力上限 done
洗澡回2點健康值 done
探索 格子效果 done

健康值低於20每次出門有機率生病，越低機率越高 done
生病會有懲罰(執行動作所需的體力加倍) done
生病強制歸零健康值，體力上限減一，生病狀態下不能玩耍，直到健康值高於40 done

新建遊戲 done
出門與睡覺icon浮動效果 done
天數 done
整理asset資料夾 done

重寫資源載入方式 done
每次建新遊戲or載入遊戲時重建主畫面 done

上班一開始等待時按方向鍵觸發
反覆餵食按鈕菜單卡住
上班第一個以後蝦雞巴按方向鍵觸發
餵食動畫有時候會卡住拍章魚(沒報錯)
生病時玩耍、訓練 不能執行 但是會扣體力 done
生病時重製遊戲動畫會維持在生病狀態
"""

def resource_path(relative_path):
    # ---- sys 取得路徑 ----
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def collect_image_paths(folder):
    # ---- 獲得assets底下所有圖片路徑 ----
    image_dict = {}
    abs_folder_path = resource_path(folder)

    for file in os.listdir(abs_folder_path):
        if file.lower().endswith((".png", ".gif")):
            name = os.path.splitext(file)[0]
            rel_path = os.path.join(folder, file)
            image_dict[name] = resource_path(rel_path)

    return image_dict

class MyApp:
    def __init__(self, root):
        
        self.image_paths = collect_image_paths("assets")

        # ---- pet stat ----
        self.hungry = 50
        self.emotion = 50
        self.health = 100
        self.day = 1
        self.is_sick = False

        # ---- player stat ----
        self.money = 500
        self.stamina = 10
        self.max_stamina = 10
        self.food_info = []

        self.custom_cursor = None
        self.selected_food = None

        # ---- normal, feeding, bathing, playing, trainning ----
        self.mode = "normal" 
        
        self.root = root
        self.root.title("寵物模擬器")
        
        self.screenWidth = root.winfo_screenwidth() # 螢幕寬度
        self.screenHeight = root.winfo_screenheight() # 螢幕高度
        self.w = 600 # 視窗寬
        self.h = 500 # 視窗高
        self.x = (self.screenWidth-self.w) / 2 # 視窗左上角x軸位置
        self.y = (self.screenHeight-self.h) / 2 # 視窗左上角Y軸位置
        self.root.geometry(f"{self.w}x{self.h}+{int(self.x)}+{int(self.y)}")

        # ---- 左側區塊 (寵物動作區)：餵食、洗澡、玩耍、訓練
        # ---- 中間區塊 (主要顯示區)：上半部是 GifPlayer（寵物動畫），下半部是 content_canvas（飢餓、開心、年齡）。
        # ---- 右側區塊 (玩家功能區)：最上方：金錢顯示（money）。下方：地圖、睡覺
 
        # ---- 主區塊（內容顯示區）----
        self.container = Frame(root, width=600, height=500)
        self.container.grid_propagate(False)
        self.container.grid(row=0, column=0, sticky=NSEW)
        
        if self.is_sick == True:
            self.root.after_idle(self.become_sick)

        # ---- 加載遊戲 ----
        self.load_game()

    def feed_action(self):
        FeedAction(self.root, self.gif_player, self).perform()

    def bath_action(self):
        BathAction(self.root, self.gif_player, self).perform()

    def play_action(self):
        PlayAction(self.root, self.gif_player, self).perform()

    def train_action(self):
        TrainAction(self.root, self.gif_player, self).perform()

    def open_map(self, event=None):
        self.player_map = PlayerMap(self.root, self)

    def on_sleep(self, event=None):
        SleepAction(self.root, self).perform()

    def become_sick(self):
        self.is_sick = True
        self.max_stamina = max(1, self.max_stamina - 1)
        self.update_stamina_display()
        self.gif_player.switch_gif(self.image_paths["sick"])
        self.show_warning_message("生病了！需要休息與治療！", self.container)

    def recover_from_sickness(self):
        self.is_sick = False
        self.gif_player.switch_gif(self.image_paths["ani_1"])
        self.show_warning_message("痊癒了！", self.container)
        
    def on_gif_click(self, event):
        if self.mode != "normal":
            return  # 在餵食、洗澡等模式中不執行點擊反應

        pat_path = self.image_paths["pat_1"]
        self.gif_player.show_static(pat_path)
        self.root.after(500, self.gif_player.play)

    def on_action_press(self, event):
        item = self.petActionCanvas.find_withtag("current")[0]
        item_info = self.action_items[item]
        rect, text, shadow, y0 = item_info["rect"], item_info["text"], item_info["shadow"], item_info["y"]
        self.petActionCanvas.itemconfig(shadow, state="hidden")
        self.petActionCanvas.scale(rect, 30, y0 + 30, 0.95, 0.95)
        self.petActionCanvas.scale(text, 30, y0 + 30, 0.95, 0.95)
        self.petActionCanvas.itemconfig(rect, fill="orange")
        self.petActionCanvas.itemconfig(text, fill="white")

    def on_action_release(self, event):
        item = self.petActionCanvas.find_withtag("current")[0]
        item_info = self.action_items[item]
        rect, text, shadow, command, y0 = (item_info["rect"], item_info["text"], item_info["shadow"], item_info["command"], item_info["y"])
        self.petActionCanvas.coords(rect, 0, y0, 60, y0 + 60)
        self.petActionCanvas.coords(text, 30, y0 + 30)
        self.petActionCanvas.itemconfig(rect, fill="white")
        self.petActionCanvas.itemconfig(text, fill="grey")
        self.petActionCanvas.itemconfig(shadow, state="normal")

        command()
        
    def apply_action_penalty(self, action_type):
        if action_type == "shop":
            self.hungry = max(0, self.hungry - 2)
            self.emotion = max(0, self.emotion - 3)
            self.health = max(0, self.health - 2)

        elif action_type == "work":
            self.hungry = max(0, self.hungry - 5)
            self.emotion = max(0, self.emotion - 20)
            self.health = max(0, self.health - 20)

        elif action_type == "gamble_win":
            self.hungry = max(0, self.hungry - 2)
            self.emotion = max(0, self.emotion + 5)
            self.health = max(0, self.health - 2)
        
        elif action_type == "gamble_lose":
            self.hungry = max(0, self.hungry - 2)
            self.emotion = max(0, self.emotion - 10)
            self.health = max(0, self.health - 2)

        elif action_type == "explore":
            self.hungry = max(0, self.hungry - 2)
            self.health = max(0, self.health - 2)

        elif action_type == "sleep":
            self.hungry = max(0, self.hungry - 20)
            self.emotion = max(0, self.emotion - 20)
            self.day += 1
        
        elif action_type == "bath":
            if(self.health >= 20):
                self.health = min(100, self.health + 2)
            else:
                self.show_warning_message("健康值不足，洗澡沒有效果...", self.container)
        
        elif action_type == "play":
            self.emotion = max(0, self.emotion + 10)

        if action_type in ["shop", "work", "gamble_win", "gamble_lose", "explore"]:
            if self.health < 20 and not self.is_sick:
                chance = (20 - self.health) * 5  # 健康越低，機率越高，最多95%
                roll = random.randint(1, 100)
                if roll <= chance:
                    self.become_sick()
                    print(f"因為執行{action_type}而生病了！(機率：{chance}%，擲骰結果：{roll})")
            
        print(f"動作{action_type}, 飢餓{self.hungry}, 心情{self.emotion}, 健康{self.health}")
        self.update_status_bars()

    def change_status(self, name, value):
        if name == "money":
            self.money += value

        elif name == "hungry":
            self.hungry = min(100, self.hungry + value)

        elif name == "emotion":
            self.emotion = min(100, self.emotion + value)

        elif name == "health":
            self.health = min(100, self.health + value)

        self.update_status_bars()
        
    def use_stamina(self, amount):
        effective_amount = amount
        if self.is_sick:
            effective_amount *= 2

        if self.stamina >= effective_amount:
            self.stamina -= effective_amount
            self.update_stamina_display()
            return True
        else:
            self.show_warning_message("體力不足，無法執行此動作。", self.container)

            return False

    def update_money_display(self):
        print(f"金錢:{self.money}")
        self.playerActionCanvas.itemconfigure(self.money_text, text="$" + str(self.money))
    
    def update_stamina_display(self):
        print(f"體力:{self.stamina}/{self.max_stamina}")
        self.playerActionCanvas.itemconfigure(self.stamina_text, text=f"體力:{self.stamina}/{self.max_stamina}")

    def update_status_bars(self):
        self.hungry = max(0, min(100, self.hungry))
        self.emotion = max(0, min(100, self.emotion))
        self.health = max(0, min(100, self.health))
        self.content_canvas.coords(self.hungry_progressbar2, 80, 15, 80+self.hungry*2, 25)
        self.content_canvas.coords(self.emo_progressbar2, 80, 45, 80+self.emotion*2, 55)
        self.content_canvas.coords(self.health_progressbar2, 80, 75, 80+self.health*2, 85)
        # 更新天數
        self.content_canvas.itemconfig(self.display_days, text=f"已經過了{self.day}天")

        self.update_money_display()
        self.update_stamina_display()
        if self.is_sick and self.health > 40:
            self.recover_from_sickness()

    def show_warning_message(self, message, parent):
        print("提示")
        parent.update_idletasks()
        main_width = parent.winfo_width()
        main_height = parent.winfo_height()
        msg_width = 250
        msg_height = 50
        self.msg_canvas = Canvas(parent, width=250, height=50, borderwidth=0, highlightthickness=1)
        self.msg_canvas.place(x=(main_width - msg_width) // 2, y=(main_height - msg_height) // 2)

        center_x, center_y = msg_width // 2, msg_height // 2
        rect = self.msg_canvas.create_rectangle(center_x - 100, center_y - 20, center_x + 100, center_y + 20, fill="white")
        text = self.msg_canvas.create_text(center_x, center_y, text=message, font=("Arial", 10), fill="grey")

        self.msg_canvas.after(2000, self.msg_canvas.destroy)

    def save_game(self):
        save_data = {
            "petName": "章魚一號",
            "hungry": self.hungry,
            "emotion": self.emotion,
            "health": self.health,
            "day": self.day,
            "is_sick" : self.is_sick,
            "money": self.money,
            "stamina": self.stamina,
            "max_stamina": self.max_stamina,
            "food": self.food_info  # food_info 原本就是 dict
        }

        try:
            with open('saved.json', 'w', encoding='utf-8') as f:
                json.dump(save_data, f, ensure_ascii=False, indent=4)
            print("遊戲進度已儲存！")
            self.show_warning_message("遊戲進度已儲存！", self.container)
        except Exception as e:
            print(f"儲存失敗: {e}")

    def load_game(self):
        try:
            with open('saved.json', 'r', encoding='utf-8') as f:
                data = json.load(f)

            # ---- pet stat ----
            self.hungry = data["hungry"]
            self.emotion = data["emotion"]
            self.health = data["health"]
            self.day = data["day"]
            self.is_sick = data["is_sick"]

            # ---- player stat ----
            self.money = data["money"]
            self.stamina = data["stamina"]
            self.max_stamina = data["max_stamina"]
            self.food_info = data["food"]

            self.build_main_screen()
            print("遊戲進度已載入！")
            self.show_warning_message("遊戲進度已載入！", self.container)

        except FileNotFoundError:
            print("找不到存檔，請先建立新遊戲。")
            self.show_warning_message("找不到存檔，請先建立新遊戲。", self.container)

        except json.JSONDecodeError:
            print("存檔格式錯誤，無法讀取。")
            self.show_warning_message("存檔格式錯誤，請確認檔案內容。", self.container)

        except Exception as e:
            print(f"載入遊戲失敗: {e}")
            self.show_warning_message("載入遊戲失敗，發生未知錯誤。", self.container)
        
    def new_game(self):
        old_file = 'saved.json'
        backup_file = 'saved(old).json'

        # 備份目前的存檔
        if os.path.exists(old_file):
            try:
                shutil.copy(old_file, backup_file)
                print(f"已備份舊存檔為{backup_file}")
            except Exception as e:
                print(f"備份失敗: {e}")
                self.show_warning_message("備份失敗，無法建立新遊戲。", self.container)
                return

        # 建立新的遊戲初始狀態
        new_data = {
            "petName": "章魚一號",
            "hungry": 50,
            "emotion": 50,
            "health": 100,
            "day": 1,
            "is_sick": False,
            "money": 500,
            "stamina": 10,
            "max_stamina": 10,
            "food": {
                "飼料1": {
                    "quantity": 0,
                    "price": 5,
                    "hunger": 5,
                    "happy": 5,
                    "cure": 0,
                    "pic": "food_1"
                },
                "飼料2": {
                    "quantity": 0,
                    "price": 10,
                    "hunger": 10,
                    "happy": 5,
                    "cure": 0,
                    "pic": "food_2"
                },
                "飼料3": {
                    "quantity": 0,
                    "price": 20,
                    "hunger": 20,
                    "happy": 20,
                    "cure": 0,
                    "pic": "food_3"
                },
                "藥品1": {
                    "quantity": 0,
                    "price": 50,
                    "hunger": 0,
                    "happy": 0,
                    "cure": 10,
                    "pic": "med_1"
                },
                "藥品2": {
                    "quantity": 0,
                    "price": 100,
                    "hunger": 0,
                    "happy": -10,
                    "cure": 50,
                    "pic": "med_2"
                }
            }
        }

        self.new_game_canvas = Canvas(self.container, width=600, height=500, highlightthickness=0)
        self.new_game_canvas.place(x=0, y=0)

        try:
            with open(old_file, 'w', encoding='utf-8') as f:
                json.dump(new_data, f, ensure_ascii=False, indent=4)
            print("已建立新遊戲存檔")
            self.show_warning_message(f"已開始新遊戲，舊檔已備份為{backup_file}", self.container)
            self.load_game()
        except Exception as e:
            print(f"建立新遊戲失敗: {e}")
            self.show_warning_message("建立新遊戲失敗！", self.container)

        self.root.after(1000, self.new_game_canvas.destroy)

    def build_main_screen(self):
            # ---- 中間GIF動畫，stat ----
            self.center_canvas = Canvas(self.container, width=300, height=500, borderwidth=0, highlightthickness=0)
            self.center_canvas.place(x=150, y=0)
            ani_path = self.image_paths["ani_1"]
            self.gif_player = GifPlayer(self.center_canvas, ani_path, 300, 300, x=0, y=0)
            self.gif_player.bind_click(self.on_gif_click)

            self.content_canvas = Canvas(self.center_canvas, width=300, height=130, bg="pink", borderwidth=0, highlightthickness=0)
            self.content_canvas.place(x=0, y=300)

            self.content_canvas.create_text(45, 20, text="飢餓值：", font=("", 10))
            self.hungry_progressbar1 = self.content_canvas.create_rectangle(80, 15, 280, 25, fill="gray", outline="black")
            self.hungry_progressbar2 = self.content_canvas.create_rectangle(80, 15, 80+self.hungry*2, 25, fill="skyblue", outline="black")

            self.content_canvas.create_text(45, 50, text="心情值：", font=("", 10))
            self.emo_progressbar1 = self.content_canvas.create_rectangle(80, 45, 280, 55, fill="gray", outline="black")
            self.emo_progressbar2 = self.content_canvas.create_rectangle(80, 45, 80+self.emotion*2, 55, fill="skyblue", outline="black")

            self.content_canvas.create_text(45, 80, text="健康值：", font=("", 10))
            self.health_progressbar1 = self.content_canvas.create_rectangle(80, 75, 280, 85, fill="gray", outline="black")
            self.health_progressbar2 = self.content_canvas.create_rectangle(80, 75, 80+self.health*2, 85, fill="skyblue", outline="black")

            self.content_canvas.create_text(45, 110, text="天數： ", font=("", 10))
            self.display_days = self.content_canvas.create_text(80, 110, text=f"已經過了{self.day}天", font=("", 10, "bold"), anchor="w")
        
            # ---- 左側寵物動作區塊 ----
            self.petActionCanvas = Canvas(self.container, width=100, height=500, highlightthickness=0)
            self.petActionCanvas.place(x=20, y=120)
            self.action_items = {}

            self.feed_action_obj = FeedAction(self.root, self.gif_player, self)
            self.bath_action_obj = BathAction(self.root, self.gif_player, self)
            self.play_action_obj = PlayAction(self.root, self.gif_player, self)
            self.train_action_obj = TrainAction(self.root, self.gif_player, self)
            
            actions = [
                ("餵食", self.feed_action_obj.perform),
                ("洗澡", self.bath_action_obj.perform),
                ("玩耍", self.play_action_obj.perform),
                ("訓練", self.train_action_obj.perform)
            ]

            for i, (label, command) in enumerate(actions):
                y0 = i * 70
                y1 = y0 + 60

                shadow = self.petActionCanvas.create_rectangle(3, y0 + 3, 63, y0 + 63, fill="grey", outline="")
                rect = self.petActionCanvas.create_rectangle(0, y0, 60, y1, outline="grey", fill="white")
                text = self.petActionCanvas.create_text(30, y0 + 30, text=label, font=("Arial", 10, "bold"), fill="grey")
                self.petActionCanvas.tag_lower(shadow, rect)

                self.action_items[rect] = {
                    "rect": rect,
                    "text": text,
                    "shadow": shadow,
                    "command": command,
                    "y": y0
                }
                self.action_items[text] = self.action_items[rect]

                self.petActionCanvas.tag_bind(rect, "<ButtonPress-1>", self.on_action_press)
                self.petActionCanvas.tag_bind(text, "<ButtonPress-1>", self.on_action_press)

                self.petActionCanvas.tag_bind(rect, "<ButtonRelease-1>", self.on_action_release)
                self.petActionCanvas.tag_bind(text, "<ButtonRelease-1>", self.on_action_release)

            # ---- 右側玩家動作 -----
            money_path = self.image_paths["money"]
            stamina_path = self.image_paths["stamina"]
            map_path = self.image_paths["map"]

            self.money_img = ImageTk.PhotoImage(Image.open(money_path).resize((40, 40)))
            self.stamina_img = ImageTk.PhotoImage(Image.open(stamina_path).resize((40, 40)))

            self.playerActionCanvas = Canvas(self.container, width=200, height=500, borderwidth=0, highlightthickness=0)
            self.playerActionCanvas.place(x=470, y=0)

            self.playerActionCanvas.create_image(40, 40, image=self.money_img)
            self.money_text = self.playerActionCanvas.create_text(40, 40, text="$" + str(self.money), font=("Arial", 12, "bold"), anchor="w")

            self.playerActionCanvas.create_image(40, 90, image=self.stamina_img)
            self.stamina_text = self.playerActionCanvas.create_text(40, 90, text=f"體力:{self.stamina}/{self.max_stamina}", font=("Arial", 12, "bold"), anchor="w")

            # 地圖 
            self.map_img_orig = Image.open(map_path).resize((60, 60))
            self.map_img = ImageTk.PhotoImage(self.map_img_orig)
            self.map_img_large = ImageTk.PhotoImage(self.map_img_orig.resize((72, 72)))
                    
            map_icon = self.playerActionCanvas.create_image(70, 250, image=self.map_img)
            self.playerActionCanvas.tag_bind(map_icon, "<Button-1>", self.open_map)
            self.playerActionCanvas.tag_bind(map_icon, "<Enter>", lambda e: self.playerActionCanvas.itemconfig(map_icon, image=self.map_img_large))
            self.playerActionCanvas.tag_bind(map_icon, "<Leave>", lambda e: self.playerActionCanvas.itemconfig(map_icon, image=self.map_img))

            # 睡覺
            sleep_path = self.image_paths["sleep"]
            self.sleep_img_orig = Image.open(sleep_path).resize((60, 60))
            self.sleep_img = ImageTk.PhotoImage(self.sleep_img_orig)
            self.sleep_img_large = ImageTk.PhotoImage(self.sleep_img_orig.resize((72, 72)))

            sleep_icon = self.playerActionCanvas.create_image(70, 350, image=self.sleep_img)
            self.playerActionCanvas.tag_bind(sleep_icon, "<Button-1>", self.on_sleep)
            self.playerActionCanvas.tag_bind(sleep_icon, "<Enter>", lambda e: self.playerActionCanvas.itemconfig(sleep_icon, image=self.sleep_img_large))
            self.playerActionCanvas.tag_bind(sleep_icon, "<Leave>", lambda e: self.playerActionCanvas.itemconfig(sleep_icon, image=self.sleep_img))

            # 建立直式選單按鈕
            self.menubar = Menu(self.root)
            self.filemenu = Menu(self.menubar, tearoff=False)
            self.menubar.add_cascade(label="檔案",menu=self.filemenu ,underline=0)
            self.filemenu.add_command(label="儲存檔案",command=self.save_game)
            self.filemenu.add_command(label="載入遊戲",command=self.load_game)
            self.filemenu.add_command(label="新建遊戲",command=self.new_game)
            self.filemenu.add_separator()
            self.filemenu.add_command(label="Exit",command=root.destroy)
            self.root.config(menu=self.menubar)

            self.update_status_bars()


class PlayerMap:
    def __init__(self, root, app):
        self.root = root
        self.app = app

        self.map_canvas = Canvas(app.container, width=600, height=500, bg="lightyellow", highlightthickness=0)
        self.map_canvas.place(x=0, y=0)
        
        #explore_selected, gamble_selected, work_selected, shop_selected, goback_selected
        self.images = {
            "default": ImageTk.PhotoImage(Image.open(self.app.image_paths["default"])),
            "shop": ImageTk.PhotoImage(Image.open(self.app.image_paths["shop_selected"])),
            "work": ImageTk.PhotoImage(Image.open(self.app.image_paths["work_selected"])),
            "gamble": ImageTk.PhotoImage(Image.open(self.app.image_paths["gamble_selected"])),
            "explore": ImageTk.PhotoImage(Image.open(self.app.image_paths["explore_selected"])),
            "goback": ImageTk.PhotoImage(Image.open(self.app.image_paths["goback_selected"])),
        }

        self.bg_image_id = self.map_canvas.create_image(0, 0, anchor="nw", image=self.images["default"])

        self.create_oval_button(100, 240, 60, "Shop", self.shopping, "shop")
        self.create_oval_button(370, 200, 60, "Work", self.working, "work")
        self.create_oval_button(220, 350, 60, "Gamble", self.gambling, "gamble")
        self.create_oval_button(430, 390, 80, "Explore", self.exploring, "explore")
        self.create_oval_button(35, 440, 30, "Go Back", self.close_map, "goback")
        

    def create_oval_button(self, x, y, r, label, command, hover_key):
        oval = self.map_canvas.create_oval(x - r, y - r, x + r, y + r, fill="", outline="")
        self.map_canvas.tag_bind(oval, "<Button-1>", command)
        
        # 綁定 hover 事件
        self.map_canvas.tag_bind(oval, "<Enter>", lambda e: self.set_background(hover_key))
        self.map_canvas.tag_bind(oval, "<Leave>", lambda e: self.set_background("default"))

    def set_background(self, key):
        self.map_canvas.itemconfig(self.bg_image_id, image=self.images[key])

    def close_map(self, event=None):
        self.map_canvas.destroy()

    def shopping(self, event=None):
        ShopAction(self.root, self.app).perform()
        self.close_map()

    def working(self, event=None):
        WorkAction(self.root, self.app).perform()
        self.close_map()

    def gambling(self, event=None):
        GambleAction(self.root, self.app).perform()
        self.close_map()

    def exploring(self, event=None):
        ExploreAction(self.root, self.app).perform()
        self.close_map()

class PlayerAction:
    def __init__(self, root, app=None):
        self.root = root
        self.app = app
       
    def perform(self):
        raise NotImplementedError("子類別必須實作 perform() 方法")

class ShopAction(PlayerAction):
    def __init__(self, root, app):
        super().__init__(root, app)
        self.app = app
        self.shop_canvas = None
        self.labels_quantity = []
        self.image_refs = {}

    def perform(self):
        if not self.app.use_stamina(1):
            return  # 體力不足，不執行後續動作
    
        self.shop_canvas = Canvas(self.app.container, width=600, height=500, bg="beige", highlightthickness=0)
        self.shop_canvas.place(x=0, y=0)

        self.playerActionCanvas = Canvas(self.shop_canvas, width=200, height=500, borderwidth=0, bg="beige", highlightthickness=0)
        self.playerActionCanvas.place(x=470, y=0)

        self.money_img = self.app.money_img
        self.playerActionCanvas.create_image(40, 40, image=self.money_img)
        self.money_text = self.playerActionCanvas.create_text(40, 40, text="$" + str(self.app.money), font=("Arial", 12, "bold"), anchor="w")
                                             
        table_frame = Frame(self.root, bg="white", bd=2, relief="solid")
        self.shop_canvas.create_window(300, 220, window=table_frame)

        headers = ["商品", "擁有數量", "價格", "操作"]
        for col, header in enumerate(headers):
            Label(table_frame, text=header, width=15, font=("Arial", 10, "bold"), bg="#f0f0f0").grid(row=0, column=col, padx=2, pady=2)

        self.labels_quantity = []
        self.food_info = self.app.food_info

        for row, (name, item) in enumerate(self.food_info.items(), start=1):
            quantity = item.get("quantity", 0)
            price = item.get("price", 0)

            pic_key = item.get("pic")
            img_path = self.app.image_paths.get(pic_key)
            
            img = Image.open(img_path).resize((30, 30))
            photo = ImageTk.PhotoImage(img)
            self.image_refs[name] = photo

            img_label = Label(table_frame, image=photo, borderwidth=1, relief="solid")
            img_label.grid(row=row, column=0, pady=2)

            # 滑鼠懸停提示名稱
            img_label.bind("<Enter>", lambda e, n=name: self.show_tooltip(e, n))
            img_label.bind("<Leave>", self.hide_tooltip)

            qty_label = Label(table_frame, text=str(quantity), width=15)
            qty_label.grid(row=row, column=1, padx=2, pady=2)
            self.labels_quantity.append((qty_label, item))

            Label(table_frame, text=str(price), width=15).grid(row=row, column=2, padx=2, pady=2)

            buy_button = Button(table_frame, text="購買", bg="orange",
                                command=lambda i=item, l=qty_label, p=price: self.buy_food(i, l, p))
            buy_button.grid(row=row, column=3, padx=2, pady=2)

        return_button = Button(self.root, text="結束購買", command=self.close_shop)
        self.shop_canvas.create_window(300, 450, window=return_button)

        # 建立 tooltip label（先不顯示）
        self.tooltip = Label(self.root, text="", bg="lightyellow", relief="solid", bd=1)
        self.tooltip.place_forget()

    def show_tooltip(self, event, name):
        self.tooltip.config(text=name)
        x = event.widget.winfo_pointerx() - self.root.winfo_rootx() + 10
        y = event.widget.winfo_pointery() - self.root.winfo_rooty() + 10
        self.tooltip.place(x=x, y=y)
        self.tooltip.lift()

    def hide_tooltip(self, event):
        self.tooltip.place_forget()

    def buy_food(self, food_item, qty_text, price):
        if self.app.money >= price:
            self.app.money -= price
            food_item["quantity"] = food_item.get("quantity", 0) + 1
            qty_text.config(text=str(food_item["quantity"]))
            self.playerActionCanvas.itemconfig(self.money_text, text=f"${self.app.money}")
            self.app.update_money_display()
        else:
            messagebox.showwarning("購買失敗", "金錢不足，無法購買！")

    def close_shop(self):
        self.app.apply_action_penalty("shop")
        self.shop_canvas.destroy()
    
class WorkAction(PlayerAction):
    def __init__(self, root, app):
        super().__init__(root, app)
        self.app = app
        self.current_work_id = 0
        self.work_id = {}
        self.work_canvas = None
        self.work_images = {}

    def perform(self):
        if not self.app.use_stamina(1):
            return  # 體力不足，不執行後續動作
        
        self.work_canvas = Canvas(self.root, width=600, height=500, bg='lightblue')
        self.work_canvas.place(x=0, y=0)
        self.canvas_ready = True
        print("畫布已成功初始化")

        # 使用 GifPlayer 播放 ani_2.gif
        try:
            ani_path = self.app.image_paths["ani_2"]
            self.gif_player = GifPlayer(self.work_canvas, ani_path, width=500, height=500, x=120, y=50)
            print("人物動畫 gif 載入成功")
        except Exception as e:
            print(f"載入 gif 動畫失敗：{e}")

        # 載入工作圖片
        try:

            self.work_images = {
                0: ImageTk.PhotoImage(Image.open(self.app.image_paths["work_pic0"])),
                1: ImageTk.PhotoImage(Image.open(self.app.image_paths["work_pic1"])),
                2: ImageTk.PhotoImage(Image.open(self.app.image_paths["work_pic2"])),
                3: ImageTk.PhotoImage(Image.open(self.app.image_paths["work_pic3"])),
            }
            for i, img in self.work_images.items():
                setattr(self.work_canvas, f"work{i}_image", img)  # 防止回收
        except Exception as e:
            print(f"工作圖片載入失敗：{e}")

        # 顯示圖片
        self.working_game = WorkingGame(self.root, self.app, self.work_canvas, self.back_to_container, self.work_images, self.gif_player)

    def back_to_container(self):
        print("返回主畫面")
        if hasattr(self, 'work_canvas') and self.work_canvas:
            self.work_canvas.destroy()
            self.work_canvas = None
            self.canvas_ready = False  # 畫布被刪除後重設狀態
            print("畫布已成功刪除")

class GambleAction(PlayerAction):
    def __init__(self, root, app):
        super().__init__(root, app)
        self.app = app

    def perform(self):
        if not self.app.use_stamina(1):
            return  # 體力不足，不執行後續動作
        self.container = Frame(self.root, width=600, height=500)
        self.container.grid(row=0, column=0, sticky=NSEW)

        # 內容區（上方）
        self.top_frame = Frame(self.container, width=600, height=200)
        self.top_frame.grid(row=0, column=0, sticky=NSEW)

        # 骰盤區（下方）
        self.plate_canvas = Canvas(self.container, width=600, height=300, background="lightblue", highlightthickness=0)
        self.plate_img = ImageTk.PhotoImage(Image.open(self.app.image_paths["die_plate"]))
        self.plate_canvas.create_image(0, 40, anchor="nw", image=self.plate_img)
        self.plate_canvas.grid(row=1, column=0, sticky="ew")

        self.money_win = 0
        self.paid_money = 50
        self.gamble_times = 1
        self.deposit_lab = Label(self.top_frame, text=f"目前存款： {self.app.money}")
        self.deposit_lab.place(x=5, y=5)

        self.faces = [
            ImageTk.PhotoImage(Image.open(self.app.image_paths[f"d{i}"]))
            for i in range(1, 7)
        ]
        self.die_label = {}
        for i in range(3):
            self.die_label[i] = Label(self.top_frame, image=self.faces[0])
            self.die_label[i].place(x=600 * 0.25 * i + 112, y=30)

        self.btn = Button(self.top_frame, text="擲骰子", command=self.roll)
        self.btn.place(x=278, y=120)
        self.btn.config(state="disabled")

        self.notice_lab = Label(self.top_frame, text="花費50選擇要下注的區域\n成功猜對骰子即獲得獎勵", relief="raised", borderwidth=1, font=("", 12))
        self.notice_lab.place(x=150, y=80, width=300, height=100)

        self.root.after(3000, self.bind_plate)
        self.last_name = ""
        self.choosed_region = ""

        self.regions = self.generate_regions(0, 40)

    def generate_regions(self, start_x=0, start_y=0):
        regions = {}
        cell_w, cell_h = 60, 58.25
        # 左區：產生 4~10（共7格，每列2格，10在右側）
        left_start_x = start_x
        top_start_y = start_y
        num = 4
        for i in range(4):  # 4列
            for j in range(2):
                if num > 10:
                    break
                # 最後一個（num==10）放右邊（j==1），跳過左邊
                if num == 10 and j == 0:
                    continue
                x1 = left_start_x + j * cell_w
                y1 = top_start_y + i * cell_h
                x2 = x1 + cell_w
                y2 = y1 + cell_h
                regions[str(num)] = (x1, y1, x2, y2)
                num += 1

        # 右區：產生 11~17（共7格，每列2格）
        right_start_x = start_x + 480
        num = 11
        for i in range(4):
            for j in range(2):
                if num > 17:
                    break
                x1 = right_start_x + j * cell_w
                y1 = top_start_y + i * cell_h
                x2 = x1 + cell_w
                y2 = y1 + cell_h
                regions[str(num)] = (x1, y1, x2, y2)
                num += 1

        # 中上列：three_same_1 ~ three_same_6（6格）
        middle_top_x = start_x + 120
        for i in range(6):
            x1 = middle_top_x + i * cell_w
            y1 = start_y
            x2 = x1 + cell_w
            y2 = y1 + cell_h
            regions[f"three_same_{i+1}"] = (x1, y1, x2, y2)

        # 中下：smaller 與 larger（2格）
        middle_y1 = start_y + cell_h
        middle_y2 = start_y + 233  # 保持與你目前的底對齊
        regions["smaller"] = (start_x + 120, middle_y1, start_x + 300, middle_y2)
        regions["larger"] = (start_x + 300, middle_y1, start_x + 480, middle_y2)

        return regions

    def bind_plate(self):
        self.plate_canvas.bind("<Button-1>", self.on_click)
        self.notice_lab.destroy()

    def roll(self):
        self.btn.config(state="disabled")
        self.plate_canvas.unbind("<Button-1>")
        self.app.money -= self.paid_money
        self.choosed_region = self.last_name
        self.deposit_lab.config(text=f"目前存款： {self.app.money}")
        self.time_count = 0
        self.dice_animate()

    def dice_animate(self):
        for i in range(3):
            face = random.choice(self.faces)
            self.die_label[i].configure(image=face)
        self.time_count += 50
        if self.time_count > 3000:
            final_faces = []
            for i in range(3):
                final_face = random.randint(1, 6)
                final_faces.append(final_face)
                self.die_label[i].configure(image=self.faces[final_face - 1])

            sum_faces = sum(final_faces)

            # 判斷中獎條件
            if self.choosed_region == str(sum_faces):
                self.money_win = self.paid_money * 11
            elif all(face == final_faces[0] for face in final_faces) and self.choosed_region == f"three_same_{final_faces[0]}":
                self.money_win = self.paid_money * 101
            elif (sum_faces > 9 and self.choosed_region == "larger") or (sum_faces < 9 and self.choosed_region == "smaller"):
                self.money_win = self.paid_money * 2
            else:
                self.money_win = 0

            self.paid_money = self.money_win if self.money_win else 50
            self.app.money += self.money_win
            self.deposit_lab.config(text=f"目前存款： {self.app.money}")

            self.ask_frame = Frame(self.container, relief="raised", borderwidth=3)
            self.ask_frame.place(x=150, y=130, width=300, height=100)

            if self.money_win > 0:
                self.app.apply_action_penalty("gamble_win")
                self.app.update_money_display()

                self.ask_lab = Label(self.ask_frame, text=f"贏了{self.money_win}，要繼續嗎?(下注將上升)", font=("", 12))
                self.ask_lab.place(x=0, y=0, width=300, height=80)
                self.ask_var = StringVar()
                self.ask_yes = Radiobutton(self.ask_frame, text="是", value="是", variable=self.ask_var,
                                           indicatoron=0, command=self.play_or_not)
                self.ask_yes.place(x=50, y=50)
                self.ask_no = Radiobutton(self.ask_frame, text="否", value="否", variable=self.ask_var,
                                          indicatoron=0, command=self.play_or_not)
                self.ask_no.place(x=120, y=50)
            else:
                self.app.apply_action_penalty("gamble_lose")
                self.app.update_money_display()

                self.ask_lab = Label(self.ask_frame, text="沒猜中，掰掰", font=("", 12))
                self.ask_lab.place(x=0, y=0, width=300, height=80)
                self.root.after(2000, self.lose)
        else:
            self.root.after(50, self.dice_animate)

    def on_click(self, event):
        self.btn.config(state="normal")
        x, y = event.x, event.y
        for region_name, (x1, y1, x2, y2) in self.regions.items():
            if x1 <= x <= x2 and y1 <= y <= y2:
                if self.last_name != region_name:
                    if hasattr(self, 'rect'):
                        self.plate_canvas.delete(self.rect)
                    margin = 2
                    self.rect = self.plate_canvas.create_rectangle(x1 + margin, y1 + margin, x2 - margin, y2 - margin, outline="red", width=3)
                    self.last_name = region_name
                return

    def play_or_not(self):
        if self.ask_var.get() == "否":
            self.container.destroy()
        else:
            self.ask_frame.destroy()
            self.btn.config(state="normal")
            self.plate_canvas.bind("<Button-1>", self.on_click)

    def lose(self):
        self.container.destroy()

class ExploreAction(PlayerAction):
    def __init__(self, root, app):
        super().__init__(root, app)
        self.app = app
        self.gif_player = None

        self.monopoly_function = {
            1: ["money", 2000],
            2: ["emotion", -30],
            3: ["emotion", 30],
            4: ["hungry", 10],
            5: ["chance"],
            6: ["emotion", 40],
            7: ["hungry", 10],
            8: ["health", -20],
            9: ["hungry", 20],
            10: [""],
            11: ["emotion", -30],
            12: ["hungry", 30],
            13: ["chance"],
            14: ["health", -30],
            15: ["hungry", 30],
            16: ["emotion", 40],
            17: ["hungry", 20],
            18: ["health", -20]
        }

    def perform(self):
        self.visit_coord = {
            1:  (50, 50),  2:  (50, 150), 3:  (50, 250), 4:  (50, 350),
            5:  (50, 450), 6:  (150, 450), 7:  (250, 450), 8:  (350, 450),
            9:  (450, 450), 10: (550, 450), 11: (550, 350), 12: (550, 250),
            13: (550, 150), 14: (550, 50), 15: (450, 50), 16: (350, 50),
            17: (250, 50), 18: (150, 50),
        }
        self.current_step = 1
        
        self.monopoly_canvas = Canvas(self.root, width=600, height=500, highlightthickness=0)
        self.monopoly_canvas.place(x=0, y=0)
        self.canvas_ready = True
        print("畫布已成功初始化")

        self.monopoly_img = ImageTk.PhotoImage(Image.open(self.app.image_paths["Monopoly"]))
        self.monopoly_canvas.create_image(0, 0, anchor="nw", image=self.monopoly_img)
        
        self.tako_x, self.tako_y = self.visit_coord[self.current_step]
        tako_small_path = self.app.image_paths["tako_small"]
        self.gif_player = GifPlayer(self.monopoly_canvas, gif_path=tako_small_path, width=70, height=70, x=self.tako_x-34, y=self.tako_y-34)
        self.octopus_id = self.gif_player.image_id
        
        self.faces = [
            ImageTk.PhotoImage(Image.open(self.app.image_paths[f"d{i}"]))
            for i in range(1, 7)
        ]
        
        self.dice_image = self.monopoly_canvas.create_image(300, 250, image=self.faces[0])

        self.monopoly_canvas.create_image(200, 250, image=self.app.money_img)
        self.money_text = self.monopoly_canvas.create_text(200, 250, text="$" + str(self.app.money), font=("Arial", 12, "bold"), anchor="center")

        self.monopoly_canvas.create_image(400, 250, image=self.app.stamina_img)
        self.stamina_text = self.monopoly_canvas.create_text(400, 250, text=f"體力:{self.app.stamina}/{self.app.max_stamina}", font=("Arial", 12, "bold"), anchor="center")
        
        self.update_button = Button(self.monopoly_canvas, text="擲骰子", command=self.roll)
        self.monopoly_canvas.create_window(200, 300, window=self.update_button)
        
        self.leave_button = Button(self.monopoly_canvas, text="離開", command=self.back_to_container)
        self.monopoly_canvas.create_window(400, 300, window=self.leave_button)

    def roll(self):
        if not self.app.use_stamina(1):
            self.back_to_container()
            return  # 體力不足，不執行後續動作
        self.app.apply_action_penalty("explore")
        self.monopoly_canvas.itemconfig(self.stamina_text, text=f"體力:{self.app.stamina}/{self.app.max_stamina}")
        self.time_count = 0
        self.dice_animate()

    def dice_animate(self):
        new_face = random.choice(self.faces)
        self.monopoly_canvas.itemconfig(self.dice_image, image=new_face)
        self.time_count += 50
        if self.time_count > 700:
            final_face = random.randint(1, 6)
            self.step_count = final_face
            self.monopoly_canvas.itemconfig(self.dice_image, image=self.faces[final_face - 1])
            self.root.after(1000, self.move_tako)
        else:
            self.root.after(50, self.dice_animate)

    def move_tako(self):
        if self.monopoly_canvas is None:
            return

        # 用左上角座標計算，因為章魚貼圖偏移了 (-34, -34)
        last_x, last_y = self.visit_coord[self.current_step]
        next_step = (self.current_step % 18) + 1
        self.target_x, self.target_y = self.visit_coord[next_step]

        # 調整為貼圖實際左上角
        last_x -= 34
        last_y -= 34
        self.target_x -= 34
        self.target_y -= 34

        self.step_x = (self.target_x - last_x) / 10
        self.step_y = (self.target_y - last_y) / 10

        self.step_count -= 1
        self.current_step = next_step

        self.tako_animate()

    def tako_animate(self):
        current_coords = self.monopoly_canvas.coords(self.octopus_id)
        current_x, current_y = current_coords

        new_x = current_x + self.step_x
        new_y = current_y + self.step_y

        if abs(new_x - self.target_x) < 2 and abs(new_y - self.target_y) < 2:
            self.monopoly_canvas.coords(self.octopus_id, self.target_x, self.target_y)
            if self.step_count > 0:
                self.root.after(500, self.move_tako)
            else:
                self.root.after(500, lambda: self.apply_monopoly_effect(self.current_step))
            return

        self.monopoly_canvas.move(self.octopus_id, self.step_x, self.step_y)
        self.root.after(50, self.tako_animate)

    def apply_monopoly_effect(self, step):
        effect = self.monopoly_function.get(step, ["", 0])
        effect_type = effect[0]

        if effect_type in ["money", "emotion", "hungry", "health"]:
            amount = effect[1]
            self.app.change_status(effect_type, amount)
            print(f"{effect_type} 變化: {amount}")
            self.app.show_warning_message(f"{effect_type} 變化: {amount}", self.monopoly_canvas)

        elif effect_type == "chance":
            available_effects = [v for v in self.monopoly_function.values() if v[0] != "chance" and v[0] != ""]
            if available_effects:
                random_effect = random.choice(available_effects)
                self.app.change_status(random_effect[0], random_effect[1])
                print(f"機會事件！{random_effect[0]} 變化: {random_effect[1]}")
                self.app.show_warning_message(f"機會事件！{random_effect[0]} 變化: {random_effect[1]}", self.monopoly_canvas)
        else:
            print("這格沒有特殊效果")
        
        self.monopoly_canvas.itemconfig(self.money_text, text="$" + str(self.app.money))

    def back_to_container(self):
        print("返回主畫面")
        self.gif_player.stop()
        self.monopoly_canvas.destroy()
        self.monopoly_canvas = None
        self.canvas_ready = False
        print("畫布已成功刪除")

class SleepAction(PlayerAction):
    def __init__(self, root, app):
        super().__init__(root, app)
        self.app = app
        self.sleep_canvas = None
        self.image_refs = {}
        self.current_increment = 0
        self.gif_player = None

    def perform(self):
        self.sleep_canvas = Canvas(self.app.container, width=600, height=500, bg="RoyalBlue3", highlightthickness=0)
        self.sleep_canvas.place(x=0, y=0)
        sleep_1_path = self.app.image_paths["sleep_1"]
        self.gif_player = GifPlayer(self.sleep_canvas, sleep_1_path, width=600, height=600, x=0, y=0)
        sleep_2_path = self.app.image_paths["sleep_2"]
        self.sleep_canvas.after(self.gif_player.total_duration, lambda: self.gif_player.switch_gif(sleep_2_path))

        self.stamina_img = PhotoImage(file=self.app.image_paths["stamina"])
        self.image_refs["stamina"] = self.stamina_img
        self.stamina_image= self.sleep_canvas.create_image(300, 100, image=self.stamina_img)
        self.stamina_text = self.sleep_canvas.create_text(300, 170, text=f"{self.app.stamina}/{self.app.max_stamina}",  font=("Arial", 20, "bold"),  fill="white")

        self.initial_hungry = self.app.hungry
        self.initial_emotion = self.app.emotion
        self.app.apply_action_penalty("sleep")

        self.root.after(500, self.update_stamina_animation)

    def update_stamina_animation(self):
        #依據每5點消耗回1點體力，最多5點
        #若消耗仍不足回1點，保底回1點
        def jump_animation(up=True, step=0):
            if step < 10:
                dy = -2 if up else 2
                self.sleep_canvas.move(self.stamina_image, 0, dy)
                self.root.after(10, jump_animation, up, step + 1)
            elif up:
                self.root.after(10, jump_animation, False, 0)
            else:
                #完成跳動後更新 stamina 並繼續下一次
                self.app.stamina = min(self.app.max_stamina, self.app.stamina + 1)
                self.current_increment += 1
                self.sleep_canvas.itemconfig(self.stamina_text, text=f"{self.app.stamina}/{self.app.max_stamina}")
                self.root.after(500, self.update_stamina_animation)

        if self.current_increment == 0:

            self.hungry_diff = max(0, self.initial_hungry - self.app.hungry)
            self.emotion_diff = max(0, self.initial_emotion - self.app.emotion)

            #若有任一為0，則只能回1點
            if self.initial_hungry == 0 or self.initial_emotion == 0:
                self.stamina_to_recover = 1
            else:
                recovery_by_hungry = self.hungry_diff // 5
                recovery_by_emotion = self.emotion_diff // 5
                self.stamina_to_recover = min(5, min(recovery_by_hungry, recovery_by_emotion))

            if self.stamina_to_recover == 0:
                self.stamina_to_recover = 1

        if self.current_increment < self.stamina_to_recover:
            jump_animation()
        else:
            self.app.update_status_bars()
            self.root.after(1000, self.back_to_container)
            self.app.save_game()

    def back_to_container(self):
        if self.gif_player:
            self.gif_player.stop()
            self.gif_player = None
        print("返回主畫面")
        self.sleep_canvas.destroy()
        self.sleep_canvas = None
        print("畫布已成功刪除")



class PetAction:
    def __init__(self, root, gif_player, app):
        self.root = root
        self.gif_player = gif_player
        self.app = app 

    def perform(self):
        raise NotImplementedError("子類別必須實作 perform() 方法")
    
class FeedAction(PetAction):
    def __init__(self, root, gif_player, app):
        super().__init__(root, gif_player, app)
        print("建立 FeedAction")
        self.animating = False
        self.selected_food = None
        self.cursor_label = None
        self.food_menu = None
        self.food_menu_open = False

    def perform(self):
        print("執行餵食")
        self.app.mode = "feeding"
        self.food_menu = Treeview(self.root, columns=("name", "quantity"), show="headings")
        self.food_menu.heading("name", text="飼料名稱")
        self.food_menu.heading("quantity", text="數量")
        self.food_menu.column("name", width=100)
        self.food_menu.column("quantity", width=60)
        self.food_menu.place(x=70, y=10, height=200)

        for food_name, food_data in self.app.food_info.items():
            quantity = food_data["quantity"]
            if quantity > 0:
                self.food_menu.insert("", "end", values=(food_name, quantity))

        self.food_menu.bind("<MouseWheel>", self.mouse_wheel)
        self.food_menu.bind("<ButtonRelease-1>", self.click_food_item)

        # 開啟 menu 標記
        self.food_menu_open = True
        self.root.after(100, lambda: self.root.bind("<Button-1>", self.check_click_outside))

    def mouse_wheel(self, event):
        if event.delta:
            self.food_menu.yview_scroll(-1 * (event.delta // 120), "units")

    def click_food_item(self, event):
        selected_item = self.food_menu.focus()
        if selected_item:
            self.item_values = self.food_menu.item(selected_item, 'values')
            self.selected_food = self.item_values[0]
            pic_key = self.app.food_info[self.selected_food].get("pic", "food")
            pic_path = self.app.image_paths.get(pic_key, self.app.image_paths.get("food"))

            # 載入圖片並轉為 PhotoImage
            food_img = Image.open(pic_path).convert("RGBA")
            self.custom_cursor = ImageTk.PhotoImage(food_img)

            # 在 canvas 上畫圖片（並記住圖片 ID）
            x = self.root.winfo_pointerx() - self.root.winfo_rootx()
            y = self.root.winfo_pointery() - self.root.winfo_rooty()
            self.cursor_image_id = self.app.center_canvas.create_image(x, y, image=self.custom_cursor, anchor="nw")
            self.root.config(cursor="none")

            self.root.bind("<Motion>", self.follow_mouse)

            # 解除原本點擊空白區域事件，改綁定餵食使用事件
            self.root.unbind("<Button-1>")
            self.root.bind("<ButtonRelease-1>", self.use_food_item)

            self.food_menu.destroy()
            self.food_menu = None
            self.food_menu_open = False

    def follow_mouse(self, event=None):
        if hasattr(self, "cursor_image_id"):
            x = self.root.winfo_pointerx() - self.root.winfo_rootx()
            y = self.root.winfo_pointery() - self.root.winfo_rooty()
            self.app.center_canvas.coords(self.cursor_image_id, x, y)

    def use_food_item(self, event):
        if self.selected_food:
            food_data = self.app.food_info[self.selected_food]
            food_data["quantity"] -= 1
            print(f"{self.selected_food} -1，剩下：{food_data['quantity']}")
            if self.animating:
                print("餵食動畫進行中，請稍後...")
                return
            
            self.animating = True
            eat_path = self.app.image_paths["eat_1"]
            self.gif_player.play_temp_gif(eat_path, duration_ms=1000)
            self.root.after(2000, self.reset_animation)

            hunger_restore = food_data.get("hunger", 0)
            happy_restore = food_data.get("happy", 0)
            cure_restore = food_data.get("cure", 0)

            self.app.hungry = min(100, self.app.hungry + hunger_restore)
            self.app.emotion = min(100, self.app.emotion + happy_restore)
            self.app.health = min(100, self.app.health + cure_restore)
            
            self.app.update_status_bars()

            self.root.config(cursor="")
            self.root.unbind("<Motion>")
            self.root.unbind("<ButtonRelease-1>")

            if hasattr(self, "cursor_image_id"):
                self.app.center_canvas.delete(self.cursor_image_id)
                del self.cursor_image_id

            self.selected_food = None
            self.app.mode = "normal"

    def check_click_outside(self, event):
        # 延遲執行，以確保 click_food_item 能先處理
        self.root.after_idle(lambda: self._close_food_menu_if_needed(event))

    def _close_food_menu_if_needed(self, event):
        if self.food_menu_open and self.food_menu:
            x, y = event.x_root, event.y_root
            fx = self.food_menu.winfo_rootx()
            fy = self.food_menu.winfo_rooty()
            fw = fx + self.food_menu.winfo_width()
            fh = fy + self.food_menu.winfo_height()
            if not (fx <= x <= fw and fy <= y <= fh):
                print("點擊到 food_menu 外部，關閉")
                self.food_menu.destroy()
                self.food_menu = None
                self.food_menu_open = False
                self.root.unbind("<Button-1>")

    def reset_animation(self):
        self.animating = False
        if self.app.is_sick and self.app.health > 40:
                self.app.recover_from_sickness()

class BathAction(PetAction):
    def __init__(self, root, gif_player, app):
        super().__init__(root, gif_player, app)
        self.app = app 
        print("建立 BathAction")
        self.animating = False

    def perform(self):
        if self.animating:
            print("洗澡動畫進行中，請稍後...")
            return

        print("執行洗澡")
        self.animating = True

        bath_path = self.app.image_paths["bath_1"]
        self.gif_player.play_temp_gif(bath_path, duration_ms=2000)
        self.root.after(2000, self.reset_animation)

    def reset_animation(self):
        self.animating = False
        self.app.apply_action_penalty("bath")

class PlayAction(PetAction):
    def __init__(self, root, gif_player, app):
        super().__init__(root,gif_player, app)
        print("建立 PlayAction")
        self.app = app
        self.center_canvas = self.app.center_canvas
        self.animating = False

    def perform(self):
        if self.animating:  # 如果動畫正在進行，就不執行
            print("動畫進行中，請稍後...")
            return
        if self.app.is_sick:
            self.app.show_warning_message("生病中不能玩耍！", self.app.container)
            return
        if not self.app.use_stamina(1):
            return  # 體力不足，不執行後續動作
        self.play_ball()
        print("執行玩耍")

    def bezier(self, t, p0, p1, p2):
        x = (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t ** 2 * p2[0]
        y = (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t ** 2 * p2[1]
        return x, y
    
    def animate(self):
        if not self.animating:
            return

        if self.ball_time <= 1:
            x, y = self.bezier(self.ball_time, self.start_point, self.control_point, self.end_point)
            self.radius -= 0.2

        elif self.ball_time <= 2:
            if not self.played_temp_gif:
                self.played_temp_gif = True
                play_path = self.app.image_paths["play_1"]
                self.gif_player.play_temp_gif(play_path, 500)

            reverse_t = self.ball_time - 1
            x, y = self.bezier(reverse_t, self.end_point, self.control_point, self.start_point)
            self.radius += 0.2

        else:
            self.reset_animation()
            return

        self.center_canvas.coords(self.ball, x - self.radius, y - self.radius, x + self.radius, y + self.radius)
        self.ball_time += 0.02
        self.animation_id = self.center_canvas.after(10, self.animate)


    def play_ball(self):
        if self.animating:
            print("動畫進行中，請稍後...")
            return

        if hasattr(self, 'animation_id'):
            self.center_canvas.after_cancel(self.animation_id)

        if hasattr(self, 'ball'):
            self.center_canvas.delete(self.ball)

        # 球的起始位置與半徑
        self.radius = 30
        self.start_point = (100, 350)
        self.control_point = (300, 120)
        self.end_point = (200, 190)

        self.ball_x, self.ball_y = self.start_point
        self.ball = self.center_canvas.create_oval(
            self.ball_x - self.radius, self.ball_y - self.radius,
            self.ball_x + self.radius, self.ball_y + self.radius,
            fill="red"
        )
        self.center_canvas.tag_raise(self.ball)

        self.ball_time = 0
        self.animating = True
        self.played_temp_gif = False
        self.animate()

    def reset_animation(self):
        self.animating = False
        self.ball_time = 0

        if hasattr(self, 'animation_id'):
            self.center_canvas.after_cancel(self.animation_id)

        if hasattr(self, 'ball'):
            self.center_canvas.delete(self.ball)

        self.app.apply_action_penalty("play")
        print(f"當前情緒{self.app.emotion}")

class TrainAction(PetAction):
    def __init__(self, root, gif_player, app):
        super().__init__(root,gif_player, app)
        print("建立 TrainAction")
        self.app = app

    def perform(self):
        if self.app.is_sick:
            self.app.show_warning_message("生病中不能訓練！", self.app.container)
            return
        if not self.app.use_stamina(1):
            return  # 體力不足，不執行後續動作
        print("執行訓練")
        game = TrainningGame(self.root, self.gif_player, self.app)
        game.training()

class TrainningGame:
    def __init__(self, root, gif_player, app):
        self.root = root
        self.app = app
        self.gif_player = gif_player

    def initialize_canvas(self):
        self.pool_canvas = Canvas(root, width=600, height=400, bg='lightblue', highlightthickness=0)
        self.pool_canvas.grid(row=0, column=0, sticky="nsew")
        self.canvas_ready = True  # 畫布初始化成功
        print("畫布已成功初始化")


    def training(self):
        # 重設狀態變數
        self.can_move = False
        self.count_number = 0
        self.current_group = 0
        self.remaining_sharks = 0
        self.sharks = {}
        
        self.initialize_canvas()  # 初始化 canvas

        # 背景圖片
        pool_path = self.app.image_paths["pool_bg"]
        self.pool = PhotoImage(file=pool_path)
        self.pool_img = self.pool_canvas.create_image(300, 200, image=self.pool)
        
        # 章魚圖片
        tako_small_path = self.app.image_paths["tako_small"]
        self.tako_positions = {
            0: (260, 10),
            1: (260, 160),
            2: (260, 310)
        }
        self.current = 1
        self.tako_x, self.tako_y = self.tako_positions[self.current]
        self.gif_player = GifPlayer(self.pool_canvas, tako_small_path, width=80, height=80, x=self.tako_x, y=self.tako_y)
        self.tako_id = self.gif_player.image_id

        # 倒數圖片
        self.three = PhotoImage(file=self.app.image_paths["three"])
        self.two = PhotoImage(file=self.app.image_paths["two"])
        self.one = PhotoImage(file=self.app.image_paths["one"])

        self.number_images = {
            0: self.three,
            1: self.two,
            2: self.one,
        }

        # 倒數開始
        root.after(1000, self.countdown)

        # 鯊魚圖片
        self.shark1 = PhotoImage(file=self.app.image_paths["shark"])
        self.shark2 = PhotoImage(file=self.app.image_paths["shark"])
        self.shark3 = PhotoImage(file=self.app.image_paths["shark"])

        # 鯊魚移動順序清單
        self.string_choose = {
            1: ["2", "12", "56"],
            2: ["26", "1245", "46"], 
            3: ["15", "3", "26"],
            4: ["5", "45", "34"],
        }
        random_choose = random.randint(1, 4)
        self.sharkstring = self.string_choose[random_choose]

        # 鯊魚對應圖片
        self.shark_images = {
            '1': self.shark1,
            '2': self.shark2,
            '3': self.shark3,
            '4': self.shark1,
            '5': self.shark2,
            '6': self.shark3,
        }

        # 鯊魚起點座標
        self.shark_start_positions = {
            '1': (50, 50),
            '2': (50, 200),
            '3': (50, 350),
            '4': (550, 50),
            '5': (550, 200),
            '6': (550, 350)
        }

        # 啟動第一組鯊魚移動
        root.after(4000, self.move_next_group)

        # 綁定上下鍵
        root.bind("<Up>", lambda event: self.move_tako("up"))
        root.bind("<Down>", lambda event: self.move_tako("down"))
        # 啟動自動結束計時
        
    def move_tako(self, direction):
        if self.can_move == False:
            return
        
        last_x, last_y = self.tako_positions[self.current]
        
        if direction == "up":
            if self.current == 0:
                return
            else:
                next = self.current - 1
        elif direction == "down":
            if self.current == 2:
                return
            else:
                next = self.current + 1
            
        self.target_x, self.target_y = self.tako_positions[next]
        self.current = next
        
        self.step_y = (self.target_y - last_y) / 5
        self.step_x = 0
        
        self.tako_animate()

    def tako_animate(self):
        if self.pool_canvas is None or self.tako_id is None:
            return
        current_coords = self.pool_canvas.coords(self.tako_id)
        current_x, current_y = current_coords

        self.tako_x = current_x + self.step_x
        self.tako_y = current_y + self.step_y
        
        if abs(self.tako_y - self.target_y) < abs(self.step_y):
            self.tako_y = self.target_y
        
        self.pool_canvas.coords(self.tako_id, self.tako_x, self.tako_y)
        if self.tako_y != self.target_y:
            self.root.after(50, self.tako_animate)
     
    def countdown(self):
        """倒數計時"""
        # 確保畫布存在
        #self.ensure_canvas_ready()
        
        if not self.canvas_ready:
            print("畫布初始化失敗，停止倒數")
            return

        # 刪除舊圖片
        if hasattr(self, 'number_img'):
            try:
                self.pool_canvas.delete(self.number_img)
            except Exception as e:
                print(f"刪除倒數圖片時發生錯誤：{e}")

        # 檢查倒數是否結束
        if self.count_number >= 3:
            self.can_move = True
            print("倒數結束，開始移動")
            return

        # 更新圖片
        try:
            self.number_img = self.pool_canvas.create_image(
                300, 200, image=self.number_images[self.count_number]
            )
            print(f"倒數 {3 - self.count_number}")
            self.count_number += 1
            # 儲存 after 任務 ID
            self.current_after_id = root.after(1000, self.countdown)
        except Exception as e:
            print(f"更新倒數圖片時發生錯誤：{e}")

    def move_next_group(self):
        """移動下一組鯊魚"""
        #self.ensure_canvas_ready()
        if not self.canvas_ready:
            print("畫布初始化失敗，無法開始移動")
            return

        # 如果所有組別都移動完畢
        if self.current_group >= len(self.sharkstring):
            print("所有鯊魚移動結束")
            self.victory()
            return

        # 取得目前組別 (如"123"或"12")
        group = self.sharkstring[self.current_group]
        self.remaining_sharks = len(group)  # 記錄尚未移動完的鯊魚數量

        # 同時啟動該組別的每一隻鯊魚
        for shark_id in group:
            start_x, start_y = self.shark_start_positions[shark_id]
            shark_image = self.shark_images[shark_id]

            # 建立鯊魚影像
            shark_img = self.pool_canvas.create_image(start_x, start_y, image=shark_image)
            self.sharks[shark_id] = {'image': shark_img, 'x': start_x, 'y': start_y}

            # 啟動鯊魚移動，並使用 lambda 將 shark_id 傳遞進去
            self.move_shark(shark_id, self.on_shark_complete)

    def move_shark(self, shark_id, callback):
        # 確認畫布是否存在
        if not self.pool_canvas:
            print(f"畫布不存在，停止鯊魚 {shark_id} 移動")
            return

        # 更新 x 座標
        if shark_id in ['1', '2', '3']:
            self.sharks[shark_id]['x'] += 5
            x = self.sharks[shark_id]['x']
            y = self.sharks[shark_id]['y']

            # 如果碰到章魚，結束遊戲
            if self.check_collision(x, y):
                self.game_over()
                return

            # 如果移動到邊界，停止動畫並刪除鯊魚
            if x > 600:
                if self.pool_canvas:
                    self.pool_canvas.delete(self.sharks[shark_id]['image'])
                print(f"鯊魚 {shark_id} 到達邊界，停止")
                callback()
                return
        else:
            self.sharks[shark_id]['x'] -= 5
            x = self.sharks[shark_id]['x']
            y = self.sharks[shark_id]['y']

            # 如果碰到章魚，結束遊戲
            if self.check_collision(x, y):
                self.game_over()
                return

            # 如果移動到邊界，停止動畫並刪除鯊魚
            if x < 0:
                if self.pool_canvas:
                    self.pool_canvas.delete(self.sharks[shark_id]['image'])
                print(f"鯊魚 {shark_id} 到達邊界，停止")
                callback()
                return

        # 更新鯊魚的位置
        if self.pool_canvas:
            self.pool_canvas.coords(self.sharks[shark_id]['image'], x, y)
            root.after(10, lambda: self.move_shark(shark_id, callback))

    def on_shark_complete(self):
        # 每完成一隻鯊魚就遞減
        self.remaining_sharks -= 1

        # 如果該組所有鯊魚都完成，移動到下一組
        if self.remaining_sharks == 0:
            self.current_group += 1
            self.move_next_group()
            
    def check_collision(self, shark_x, shark_y):
        """檢查鯊魚與章魚是否碰撞"""
        tako_coords = self.pool_canvas.coords(self.tako_id)
        if not tako_coords:
            return False
        tako_x, tako_y = tako_coords
        tako_x = tako_x + 35
        tako_y = tako_y + 35

        dx = abs(tako_x - shark_x)
        dy = abs(tako_y - shark_y)
        distance = (dx ** 2 + dy ** 2) ** 0.5

        #print(tako_x, tako_y, shark_x, shark_y, distance)

        return distance < 35

    def game_over(self):
        # 清除所有鯊魚影像
        if hasattr(self, 'sharks'):
            for shark_id in list(self.sharks.keys()):
                try:
                    if self.pool_canvas:  # 確認畫布存在
                        self.pool_canvas.delete(self.sharks[shark_id]['image'])
                except Exception as e:
                    print(f"刪除鯊魚影像時發生錯誤：{e}")
        # 清除章魚影像
        if hasattr(self, 'tako2_img') and self.pool_canvas:
            try:
                self.pool_canvas.delete(self.tako2_img)
            except Exception as e:
                print(f"刪除章魚影像時發生錯誤：{e}")
        print("經過了show game over")
        self.can_move = False
        
        try:
            self.game_over_img = PhotoImage(file=self.app.image_paths["game_over"])
            if self.pool_canvas:  # 確保畫布存在
                self.pool_canvas.create_image(300, 200, image=self.game_over_img)
            print("遊戲結束！章魚被鯊魚吃掉！")
        except Exception as e:
            print(f"顯示遊戲結束畫面時發生錯誤：{e}")
        self.root.after(1000, self.back_to_container)

    def victory(self):
        self.app.max_stamina += 1
        self.pool_canvas.create_text(300, 200, text="勝利！體力上限 +1", font=("Arial", 24, "bold"), fill="green")
        print(f"{self.app.max_stamina}")
        self.app.update_status_bars()
        self.root.after(2000, self.back_to_container)

    def back_to_container(self):
        print("返回主畫面")
        self.pool_canvas.destroy()
        self.pool_canvas = None
        self.canvas_ready = False  # 畫布被刪除後重設狀態

class WorkingGame:
    def __init__(self, root, app, canvas, on_complete_callback, work_images, gif_player):
        self.root = root
        self.app = app
        self.canvas = canvas
        self.on_complete = on_complete_callback
        self.work_images = work_images  # Dict[int, PhotoImage]
        self.gif_player = gif_player

        self.round = 0
        self.total_rounds = 4
        self.used_directions = []
        self.direction_box = None
        self.direction_text = None
        self.countdown_text = None
        self.expected_direction = None
        self.response_timer = None
        self.input_received = False
        self.image_id = None
        self.correct_count = 0

        self.cd_images = [
            PhotoImage(file=self.app.image_paths["cd3"]),
            PhotoImage(file=self.app.image_paths["cd2"]),
            PhotoImage(file=self.app.image_paths["cd1"])
         ]

        self.directions = {
            "Up": "↑",
            "Down": "↓",
            "Left": "←",
            "Right": "→"
        }

        self.root.bind("<KeyRelease>", self.check_key)
        self.show_start_image()

    def show_start_image(self):
        if self.image_id:
            self.canvas.delete(self.image_id)
        self.image_id = self.canvas.create_image(200, 100, image=self.work_images[0])
        # 3秒後刪除圖片並開始遊戲
        self.root.after(3000, lambda: (self.canvas.delete(self.image_id), setattr(self, "image_id", None), self.start_next_round()))

    def start_next_round(self):
        if self.direction_text:
            self.canvas.delete(self.direction_text)
            self.direction_text = None
        
        if self.direction_box:
            self.canvas.delete(self.direction_box)
            self.direction_box = None


        if self.round >= self.total_rounds:
            self.end_game()
            return

        self.round += 1
        self.expected_direction = self.get_unique_direction()
        self.count = 3
        self.input_received = False
        self.show_countdown()

    def get_unique_direction(self):
        remaining = list(set(self.directions.keys()) - set(self.used_directions))
        dir_choice = random.choice(remaining)
        self.used_directions.append(dir_choice)
        return dir_choice

    def show_countdown(self):
        if self.countdown_text:
            self.canvas.delete(self.countdown_text)

        if self.count > 0:
            self.countdown_text = self.canvas.create_image(200, 100, image=self.cd_images[3 - self.count])
    
        if self.count > 0:
            self.count -= 1
            self.root.after(500, self.show_countdown)
        else:
            self.canvas.delete(self.countdown_text)
            self.countdown_text = None
            self.show_direction()

    def show_direction(self):
        self.direction_box = self.canvas.create_rectangle(
            150, 50, 250, 150,  fill="white", outline="black", width=2,
        )
        self.direction_text = self.canvas.create_text(
            200, 95, text=self.directions[self.expected_direction], font=("Arial", 48), fill="black"
        )
        self.response_timer = self.root.after(600, self.handle_no_input)

    def handle_no_input(self):
        if not self.input_received:
            print(f"超時 應為 {self.expected_direction}")
            self.canvas.itemconfig(self.direction_box, fill="red")
            self.canvas.itemconfig(self.direction_text, fill="white")
        
            self.gif_player.show_static(self.app.image_paths["ani_3"])
            self.shake_canvas()
            self.root.after(600, self.gif_player.reload_main_gif)

            self.expected_direction = None
            self.root.after(500, self.start_next_round)

    def check_key(self, event):
        if self.expected_direction is None or self.input_received:
            return

        self.input_received = True
        self.root.after_cancel(self.response_timer)

        if event.keysym == self.expected_direction:
            print(f"正確按鍵: {event.keysym}")
            self.correct_count += 1
            self.canvas.itemconfig(self.direction_box, fill="green")
            self.canvas.itemconfig(self.direction_text, fill="white")
        else:
            print(f"錯誤按鍵: {event.keysym}，應為 {self.expected_direction}")
            self.canvas.itemconfig(self.direction_box, fill="red")
            self.canvas.itemconfig(self.direction_text, fill="white")

            self.gif_player.show_static(self.app.image_paths["ani_3"])
            self.shake_canvas()
            self.root.after(600, self.gif_player.reload_main_gif)

        self.expected_direction = None
        self.root.after(500, self.start_next_round)

    def end_game(self):
        self.root.unbind("<KeyRelease>")
        if self.direction_text:
            self.canvas.delete(self.direction_text)
            self.direction_text = None

        if self.image_id:
            self.canvas.delete(self.image_id)      

        earned_money = self.correct_count * 10  
        self.app.money += (60 + earned_money)
        print(f"工作獲得{60+earned_money}元")
        self.app.update_money_display()
        self.app.apply_action_penalty("work")

        # 顯示隨機一張結束圖片 (work_pic1,2,3)
        final_choice = random.choice([1, 2, 3])
        self.image_id = self.canvas.create_image(200, 100, image=self.work_images[final_choice])
        print(f"顯示結束圖：assets/work_pic{final_choice}.png")

        self.root.after(3000, self.on_complete)

    def shake_canvas(self, intensity=2, duration=300):
        original_x = self.canvas.winfo_x()
        original_y = self.canvas.winfo_y()

        def shake(count=0):
            if count >= duration // 50:
                self.canvas.place(x=original_x, y=original_y)
                return
            offset_x = random.randint(-intensity, intensity)
            offset_y = random.randint(-intensity, intensity)
            self.canvas.place(x=original_x + offset_x, y=original_y + offset_y)
            self.root.after(50, lambda: shake(count + 1))

        self.canvas.place(x=original_x, y=original_y)
        shake()

class GifPlayer:
    def __init__(self, canvas, gif_path, width, height, x=0, y=0):
        self.canvas = canvas
        self.gif_path = gif_path
        self.width = width
        self.height = height
        self.x = x
        self.y = y

        self.frames = []
        self.durations = []
        self.index = 0
        self.after_id = None
        self.image_id = None
        self.original_gif_path = gif_path  # 保留主動畫路徑

        self.load_gif(gif_path)
        self.play()

    def load_gif(self, path):
        self.frames.clear()
        self.durations.clear()
        self.total_duration = 0
        gif = Image.open(path)
        for frame in ImageSequence.Iterator(gif):
            frame = frame.convert("RGBA").resize((self.width, self.height))
            self.frames.append(ImageTk.PhotoImage(frame))
            dur = frame.info.get('duration', 100)
            self.durations.append(max(dur, 20))
            self.total_duration += dur

    def play(self):
        if self.after_id:
            self.canvas.after_cancel(self.after_id)
        if not self.frames:
            return
        if self.image_id is None:
            self.image_id = self.canvas.create_image(self.x, self.y, anchor="nw", image=self.frames[self.index])
        else:
            self.canvas.itemconfig(self.image_id, image=self.frames[self.index])
        delay = self.durations[self.index]
        self.index = (self.index + 1) % len(self.frames)
        self.after_id = self.canvas.after(delay, self.play)

    def stop(self):
        if self.after_id:
            self.canvas.after_cancel(self.after_id)
            self.after_id = None

    def show_static(self, image_path):
        self.stop()
        static_img = Image.open(image_path).resize((self.width, self.height))
        self.static_photo = ImageTk.PhotoImage(static_img)
        if self.image_id is None:
            self.image_id = self.canvas.create_image(self.x, self.y, anchor="nw", image=self.static_photo)
        else:
            self.canvas.itemconfig(self.image_id, image=self.static_photo)

    def switch_gif(self, new_gif_path):
        self.stop()
        self.gif_path = new_gif_path
        self.original_gif_path = new_gif_path
        self.load_gif(new_gif_path)
        self.index = 0
        self.play()

    def play_temp_gif(self, temp_gif_path, duration_ms):
        self.stop()
        self.index = 0  # 確保從第一幀開始
        self.frames.clear()
        self.durations.clear()
        self.load_gif(temp_gif_path)

        self.play()
        self.canvas.after(duration_ms, self.reload_main_gif)

    def reload_main_gif(self):
        self.stop()
        self.load_gif(self.original_gif_path)
        self.index = 0
        self.play()

    def bind_click(self, func):
        if self.image_id is not None:
            self.canvas.tag_bind(self.image_id, "<ButtonRelease-1>", func)
        
# 啟動程式
if __name__ == "__main__":
    root = Tk()
    app = MyApp(root)
    root.mainloop()