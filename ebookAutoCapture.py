from tkinter import *
from tkinter import ttk
from tkinter import filedialog
import pyautogui
import mss
import mss.tools
import random
from datetime import datetime
from PIL import Image
import io
import ctypes

# Windows DPI 인식 설정 — 배율(125%, 150% 등) 무시하고 실제 픽셀 그대로 캡처
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)  # Per-monitor DPI aware
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()   # fallback
    except Exception:
        pass

class ebookToPDF:
    def __init__(self, root):
        self.x1 = 0
        self.y1 = 0
        self.x2 = 0
        self.y2 = 0

        self.posDisplay1 = StringVar()
        self.posDisplay2 = StringVar()
        self.posDisplay1.set("[0,0]")
        self.posDisplay2.set("[0,0]")

        self.pages = IntVar()
        self.name = StringVar()
        self.dirPath = StringVar()
        self.captureSpeedMin = IntVar()
        self.captureSpeedMax = IntVar()
        self.captureSpeedMin.set(200)
        self.captureSpeedMax.set(500)
        self.moveToNextPageOption = IntVar()
        self.progress = DoubleVar()
        self.progress.set(0.0)

        # 스크롤 캡처 관련
        self.scrollCaptureEnabled = BooleanVar()
        self.scrollCaptureEnabled.set(False)
        self.scrollCount = IntVar()
        self.scrollCount.set(3)
        self.scrollAmount = IntVar()   # 한 번 스크롤 시 휠 클릭 수
        self.scrollAmount.set(5)

        root.title("eBookAutoCapture")
        root.geometry("")
        root.resizable(width=False, height=False)

        contents = ttk.Frame(root, padding="3 3 3 3")
        contents.grid(column=0, row=0, sticky=(N, W, E, S))
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)

        ttk.Label(contents, text="madeBy p0tat0-113").grid(column=1, row=1, columnspan=3, sticky=W)
        ttk.Label(contents, text="설정 버튼을 누른 후 space키를 눌러야 좌표가 기입됨").grid(column=1, row=2, columnspan=3, sticky=W)

        ttk.Label(contents, text="좌측 상단 좌표").grid(column=1, row=3, sticky=W)
        ttk.Label(contents, text="우측 하단 좌표").grid(column=1, row=4, sticky=W)
        ttk.Label(contents, textvariable=self.posDisplay1, width=10).grid(column=2, row=3, sticky=(W, E))
        ttk.Label(contents, textvariable=self.posDisplay2, width=10).grid(column=2, row=4, sticky=(W, E))
        ttk.Button(contents, text="좌표 설정", command=self.callGetPointerPosLeft).grid(column=3, row=3, sticky=(W, E))
        ttk.Button(contents, text="좌표 설정", command=self.callGetPointerPosRight).grid(column=3, row=4, sticky=(W, E))

        ttk.Label(contents, text="총 페이지 수").grid(column=1, row=5, sticky=W)
        ttk.Label(contents, text="파일 이름").grid(column=1, row=6, sticky=W)
        ttk.Entry(contents, width=10, textvariable=self.pages).grid(column=3, row=5, sticky=(W, E))
        ttk.Entry(contents, width=10, textvariable=self.name).grid(column=3, row=6, sticky=(W, E))

        ttk.Label(contents, text="캡처 간격 최솟값(ms)").grid(column=1, row=7, sticky=W)
        ttk.Label(contents, textvariable=self.captureSpeedMin, width=5).grid(column=2, row=7, sticky=(W, E))
        ttk.Scale(contents, orient=HORIZONTAL, length=100, from_=1, to=1000,
                  variable=self.captureSpeedMin,
                  command=lambda v: self._clamp_min(v)).grid(column=3, row=7, sticky=(W, E))

        ttk.Label(contents, text="캡처 간격 최댓값(ms)").grid(column=1, row=8, sticky=W)
        ttk.Label(contents, textvariable=self.captureSpeedMax, width=5).grid(column=2, row=8, sticky=(W, E))
        ttk.Scale(contents, orient=HORIZONTAL, length=100, from_=1, to=1000,
                  variable=self.captureSpeedMax,
                  command=lambda v: self._clamp_max(v)).grid(column=3, row=8, sticky=(W, E))

        ttk.Label(contents, text="다음 페이지 이동").grid(column=1, row=9, sticky=W)
        ttk.Radiobutton(contents, text="키보드 방향키", variable=self.moveToNextPageOption, value=0).grid(column=2, row=9, sticky=W)
        ttk.Radiobutton(contents, text="마우스 클릭", variable=self.moveToNextPageOption, value=1).grid(column=3, row=9, sticky=W)

        # 구분선
        ttk.Separator(contents, orient=HORIZONTAL).grid(column=1, row=10, columnspan=3, sticky=(W, E), pady=2)

        # 스크롤 캡처 옵션
        ttk.Checkbutton(contents, text="스크롤 캡처 모드 (확대 페이지 전체 캡처)",
                        variable=self.scrollCaptureEnabled,
                        command=self._toggle_scroll_options).grid(column=1, row=11, columnspan=3, sticky=W)

        self.scrollCountLabel = ttk.Label(contents, text="스크롤 횟수")
        self.scrollCountLabel.grid(column=1, row=12, sticky=W)
        self.scrollCountDisp = ttk.Label(contents, textvariable=self.scrollCount, width=3)
        self.scrollCountDisp.grid(column=2, row=12, sticky=(W, E))
        self.scrollCountScale = ttk.Scale(contents, orient=HORIZONTAL, length=100, from_=1, to=20,
                                          variable=self.scrollCount,
                                          command=lambda v: self.scrollCount.set(round(float(v))))
        self.scrollCountScale.grid(column=3, row=12, sticky=(W, E))

        self.scrollAmountLabel = ttk.Label(contents, text="스크롤 강도 (휠 클릭 수)")
        self.scrollAmountLabel.grid(column=1, row=13, sticky=W)
        self.scrollAmountDisp = ttk.Label(contents, textvariable=self.scrollAmount, width=3)
        self.scrollAmountDisp.grid(column=2, row=13, sticky=(W, E))
        self.scrollAmountScale = ttk.Scale(contents, orient=HORIZONTAL, length=100, from_=1, to=20,
                                           variable=self.scrollAmount,
                                           command=lambda v: self.scrollAmount.set(round(float(v))))
        self.scrollAmountScale.grid(column=3, row=13, sticky=(W, E))

        self._toggle_scroll_options()  # 초기 비활성화

        ttk.Progressbar(contents, orient=HORIZONTAL, length=30, mode='determinate',
                        maximum=10000, variable=self.progress).grid(column=1, row=14, columnspan=3, sticky=(W, E))
        ttk.Button(contents, text="작업 시작", command=self.captureCall).grid(column=1, row=15, columnspan=3, sticky=(W, E))
        ttk.Button(contents, text="저장 경로 설정", command=self.getDirPath).grid(column=1, row=16, columnspan=3, sticky=(W, E))
        ttk.Label(contents, text="경로", textvariable=self.dirPath, width=51).grid(column=1, row=17, columnspan=3, sticky=W)

        for child in contents.winfo_children():
            child.grid_configure(padx=5, pady=5)

    def _toggle_scroll_options(self):
        state = NORMAL if self.scrollCaptureEnabled.get() else DISABLED
        for w in [self.scrollCountLabel, self.scrollCountDisp, self.scrollCountScale,
                  self.scrollAmountLabel, self.scrollAmountDisp, self.scrollAmountScale]:
            w.configure(state=state)

    def _clamp_min(self, v):
        val = round(float(v))
        self.captureSpeedMin.set(val)
        if val > self.captureSpeedMax.get():
            self.captureSpeedMax.set(val)

    def _clamp_max(self, v):
        val = round(float(v))
        self.captureSpeedMax.set(val)
        if val < self.captureSpeedMin.get():
            self.captureSpeedMin.set(val)

    def callGetPointerPosLeft(self, *args):
        root.bind("<Key-space>", lambda event: self.getPointerPos(event, 1))
        root.focus_set()

    def callGetPointerPosRight(self, *args):
        root.bind("<Key-space>", lambda event: self.getPointerPos(event, 2))
        root.focus_set()

    def getPointerPos(self, event, position):
        posx, posy = pyautogui.position()
        if position == 1:
            self.x1 = posx
            self.y1 = posy
            self.posDisplay1.set(str([posx, posy]))
        if position == 2:
            self.x2 = posx
            self.y2 = posy
            self.posDisplay2.set(str([posx, posy]))

    def getDirPath(self, *args):
        self.dirPath.set(filedialog.askdirectory())

    def captureCall(self, *args):
        capture = Capture()
        capture \
            .setRoot(root) \
            .setRegion(self.x1, self.y1, self.x2, self.y2) \
            .setPages(self.pages.get()) \
            .setName(self.name.get()) \
            .setDirpath(self.dirPath.get()) \
            .setCaptureSpeedRange(self.captureSpeedMin.get(), self.captureSpeedMax.get()) \
            .setProgres(self.progress) \
            .setMoveToNextPage(self.moveToNextPageOption.get()) \
            .setScrollCapture(
                self.scrollCaptureEnabled.get(),
                self.scrollCount.get(),
                self.scrollAmount.get()
            )
        root.after(2000, capture.process)


class Capture:
    def __init__(self):
        self.root = None
        self.region = None
        self.pages = None
        self.name = None
        self.dirpath = None
        self.captureSpeedMin = None
        self.captureSpeedMax = None
        self.progress = None
        self.moveToNextPage = None
        self.count = 1
        self.scrollCaptureEnabled = False
        self.scrollCount = 3
        self.scrollAmount = 5

    def setRoot(self, root):
        self.root = root
        return self

    def setRegion(self, x1, y1, x2, y2):
        self.region = (x1, y1, x2 - x1, y2 - y1)
        return self

    def setPages(self, pages):
        self.pages = pages
        return self

    def setName(self, name):
        self.name = name
        return self

    def setDirpath(self, dirpath):
        self.dirpath = dirpath.replace("/", "\\")
        return self

    def setCaptureSpeedRange(self, min_ms, max_ms):
        self.captureSpeedMin = min_ms
        self.captureSpeedMax = max_ms
        return self

    def setProgres(self, progress):
        self.progress = progress
        progress.set(0.0)
        return self

    def setMoveToNextPage(self, option):
        self.moveToNextPage = self.selectMoveToNextPageOption(option)
        return self

    def setScrollCapture(self, enabled, scroll_count, scroll_amount):
        self.scrollCaptureEnabled = enabled
        self.scrollCount = scroll_count
        self.scrollAmount = scroll_amount
        return self

    def process(self):
        if self.scrollCaptureEnabled:
            self.captureWithScroll()
        else:
            self.capture()

        self.progress.set(self.progress.get() + (10000 / self.pages))
        self.moveToNextPage()
        self.count += 1

        if self.count <= self.pages:
            # 40장 캡처마다 10~12초 휴식
            if (self.count - 1) % 40 == 0 and self.count > 1:
                delay = random.randint(10000, 12000)
                print(f"{self.count - 1}장 완료 — {delay/1000:.1f}초 휴식 중...")
            else:
                delay = random.randint(self.captureSpeedMin, self.captureSpeedMax)
            root.after(delay, self.process)
        else:
            print("작업 완료")

    def _grab_region(self):
        """현재 캡처 영역을 PIL Image로 반환"""
        with mss.mss() as sct:
            monitor = {"top": self.region[1], "left": self.region[0],
                       "width": self.region[2], "height": self.region[3]}
            shot = sct.grab(monitor)
            return Image.frombytes("RGB", shot.size, shot.rgb)

    def capture(self):
        """일반 캡처: 단일 PNG 저장"""
        now = datetime.now().strftime("%Y%m%d-%H%M%S")
        save_dir = f"{self.dirpath}\\{self.name}[{self.count}]{now}.png"
        img = self._grab_region()
        img.save(save_dir, format="PNG", optimize=False, compress_level=0)  # 무손실 최고화질
        print(save_dir)

    def captureWithScroll(self):
        """스크롤 캡처: 스크롤하며 여러 장 찍고 수직으로 이어붙여 1장으로 저장"""
        now = datetime.now().strftime("%Y%m%d-%H%M%S")
        save_dir = f"{self.dirpath}\\{self.name}[{self.count}]{now}.png"

        # 캡처 영역 중앙으로 마우스 이동 (스크롤 이벤트 수신을 위해)
        cx = self.region[0] + self.region[2] // 2
        cy = self.region[1] + self.region[3] // 2
        pyautogui.moveTo(cx, cy)

        frames = []
        frames.append(self._grab_region())  # 첫 번째 캡처

        for _ in range(self.scrollCount):
            pyautogui.scroll(-self.scrollAmount)  # 아래로 스크롤
            import time; time.sleep(0.15)          # 렌더링 대기
            frames.append(self._grab_region())

        # 수직 이어붙이기
        total_h = sum(f.height for f in frames)
        combined = Image.new("RGB", (frames[0].width, total_h))
        y_offset = 0
        for f in frames:
            combined.paste(f, (0, y_offset))
            y_offset += f.height

        combined.save(save_dir, format="PNG", optimize=False, compress_level=0)  # 무손실 최고화질
        print(f"스크롤 캡처 저장: {save_dir} ({len(frames)}장 합성)")

    def selectMoveToNextPageOption(self, num):
        if num == 0:
            return self.moveToNextPageWithKey
        elif num == 1:
            return self.moveToNextPageWithClick

    def moveToNextPageWithKey(self):
        pyautogui.press("right")
        print("키보드 딸칵")

    def moveToNextPageWithClick(self):
        pyautogui.leftClick()
        print("마우스 딸칵")


root = Tk()
ebookToPDF(root)
root.mainloop()
