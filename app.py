import cv2
import numpy as np
import time
import math
import pygame
import tkinter as tk
from tkinter import simpledialog, messagebox
import os
import sys

# Pythonファイルのあるディレクトリを基準にファイルパスを取得する関数
def resource_path(relative_path):
    base_path = os.path.dirname(os.path.abspath(__file__))  # Pythonファイルのディレクトリ
    return os.path.join(base_path, relative_path)

# tkinterを初期化
root = tk.Tk()
root.withdraw()  # メインウィンドウを非表示にする

# 操作方法のメッセージを表示
messagebox.showinfo(
    "操作方法",
    "このプログラムでは、カメラから映像を読み込み、スカウター風のエフェクトを表示します。\n\n"
    "操作方法:\n"
    "- 's'キー: 再測定を開始\n"
    "- 'q'キー: プログラムを終了\n\n"
    "スカウター番号を入力してください。"
)

# スカウター番号の入力ウィンドウを表示
camera_number = simpledialog.askinteger("スカウター選択", "スカウター番号を入力してください (例: 0, 1, 2):")

if camera_number is None:
    print("スカウター番号が入力されませんでした。プログラムを終了します。")
    exit()

# 戦闘力の目標値と増加速度を設定
target_power_level = 9000     # 目標戦闘力
increase_speed = 100          # 戦闘力が100増えるごとにかかる速度
increase_interval = 0.2       # 戦闘力100増加にかかる時間（秒）

# 自動計算された測定時間
total_duration = (target_power_level / increase_speed) * increase_interval
current_power_level = 0  # 初期値を0に設定
start_time = time.time()

# 音声ファイルの準備
pygame.mixer.init()
start_sound = pygame.mixer.Sound(resource_path("start.wav"))      # 起動時の音声
beep_sound = pygame.mixer.Sound(resource_path("beep.wav"))        # 測定中の連続音
completion_sound = pygame.mixer.Sound(resource_path("complete.wav"))  # 数値到達時の音声
beep_interval = 0.15  # 音声再生の間隔（測定中）
last_beep_time = time.time()  # 最後に音を再生した時間

# 起動時に1回だけ再生
start_sound.play()

# 顔検出用のカスケード分類器を読み込む
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

# カメラ映像のキャプチャ（指定されたカメラ番号を使用）
cap = cv2.VideoCapture(camera_number)

# カメラが正常に開かれたか確認
if not cap.isOpened():
    print(f"スカウター番号 {camera_number} は使用できません。プログラムを終了します。")
    pygame.mixer.quit()
    exit()

# ウィンドウの設定
window_name = 'Scouter Effect with White Circles and Outward Triangles'
cv2.namedWindow(window_name, cv2.WND_PROP_FULLSCREEN)
cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

print(f"Total duration calculated: {total_duration:.2f} seconds")  # デバッグ出力

def reset_measurement():
    global start_time, current_power_level, last_beep_time
    start_time = time.time()
    current_power_level = 0
    last_beep_time = time.time()
    start_sound.play()  # 再測定開始時に再度起動音を再生

reset_measurement()  # 初回の測定を開始

while True:
    # フレームの取得
    ret, frame = cap.read()
    if not ret:
        break

    # グリーンフィルターを適用
    green_filter = np.zeros_like(frame)
    green_filter[:, :, 1] = frame[:, :, 1]  # 緑のチャンネルのみ保持

    # 元のフレームとグリーンフィルターをブレンドして、フィルターを強くする
    blended_frame = cv2.addWeighted(frame, 0.4, green_filter, 0.6, 0)  # 40%の元の画像 + 60%のグリーンフィルター

    # 経過時間に基づいて戦闘力を計算
    elapsed_time = time.time() - start_time
    if elapsed_time < total_duration:
        # 目標値に向かって徐々に増加
        current_power_level = int((elapsed_time / increase_interval) * increase_speed)
        if current_power_level > target_power_level:
            current_power_level = target_power_level

        # 設定した間隔で「ピピピピ」音を再生
        if time.time() - last_beep_time > beep_interval:
            beep_sound.play()
            last_beep_time = time.time()  # 最後に音を再生した時間を更新
    else:
        # 測定時間経過後、戦闘力を目標値に固定し音を停止
        if current_power_level < target_power_level:
            completion_sound.play()  # 数値到達時の音を再生
        current_power_level = target_power_level
        beep_sound.stop()  # 測定中の音を停止

    # デバッグ出力（ターミナルで確認）
    print(f"Elapsed Time: {elapsed_time:.2f} seconds, Current Power Level: {current_power_level}")

    # 顔検出
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.3, minNeighbors=3)

    for (x, y, w, h) in faces:
        # スカウター風の白い円を描画
        center = (x + w // 2, y + h // 2)
        radius = int(w * 0.6)
        cv2.circle(blended_frame, center, radius, (255, 255, 255), 2)  # 白い円

        # 三角形の距離オフセットと大きさ
        triangle_offset = int(radius * 1.2)  # 円の外側
        triangle_size = int(radius * 0.2)    # 三角形の大きさ

        # 三角形の頂点座標を計算して描画
        triangle_positions = [
            (center[0], center[1] - triangle_offset),   # 上
            (center[0] + triangle_offset, center[1]),   # 右
            (center[0], center[1] + triangle_offset),   # 下
            (center[0] - triangle_offset, center[1])    # 左
        ]
        angles = [90, 180, 270, 0]  # 各方向の角度（頂点が中心に向く）

        for i, pos in enumerate(triangle_positions):
            angle = angles[i]
            triangle_pts = np.array([
                (pos[0] + int(triangle_size * math.cos(math.radians(angle))),
                 pos[1] + int(triangle_size * math.sin(math.radians(angle)))),
                (pos[0] + int(triangle_size * math.cos(math.radians(angle + 120))),
                 pos[1] + int(triangle_size * math.sin(math.radians(angle + 120)))),
                (pos[0] + int(triangle_size * math.cos(math.radians(angle + 240))),
                 pos[1] + int(triangle_size * math.sin(math.radians(angle + 240))))
            ])
            cv2.drawContours(blended_frame, [triangle_pts], 0, (255, 255, 255), -1)  # 白い三角形

        # 戦闘力の数値をサークルのさらに外に表示し、顔の中心から戦闘力まで線を描画
        offset_distance = radius * 2  # サークルからさらに離す距離
        text_position = (center[0] + offset_distance, center[1] - offset_distance)  # 右上に配置
        cv2.line(blended_frame, center, text_position, (255, 255, 255), 1)  # 白い線
        cv2.putText(blended_frame, str(current_power_level), text_position, cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 2)

    # フィルタを適用したフレームをフルスクリーンで表示
    cv2.imshow(window_name, blended_frame)

    # キーボードの入力を確認
    key = cv2.waitKey(1)
    if key & 0xFF == ord('q'):  # 'q'キーで終了
        beep_sound.stop()  # プログラム終了時に音も停止
        break
    elif key & 0xFF == ord('s'):  # 's'キーで再測定を開始
        reset_measurement()  # 測定のリセット

# リソース解放
cap.release()
cv2.destroyAllWindows()
pygame.mixer.quit()
