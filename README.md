RPi_EnvSensor
=============

Softwares for RPi_EnvSensor board by Switch Science Inc.

> ATTiny  ------------  ATTiny85に書き込まれたファームウェアの格納ディレクトリ
   +  main.c  ------------  初期化、メインループ、ADコンバータ関連の処理
   +  I2Cslave.h  --------  ファームウェア全体で使われる define
   +  USI_TWI_Slave.c  ---  USI を使った I2C バス関連の処理（サブルーチンと割り込み処理）
   +  USI_TWI_Slave.h  ---  I2Cバス関連の define

> Python_RPi  --------  Raspberry Pi 用の Python スクリプトの格納ディレクトリ
   +  i2c_Sensor3.py  ----  センサー基板をドライブするサンプルアプリ（β版）

　※サンプルアプリは「Python3 + Quick2wireライブラリ（モジュール）」の環境で動きます。

