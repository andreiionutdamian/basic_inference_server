# -*- coding: utf-8 -*-
"""
Copyright (C) 2017-2021 Andrei Damian, andrei.damian@me.com,  All rights reserved.

This software and its associated documentation are the exclusive property of the creator.
Unauthorized use, copying, or distribution of this software, or any portion thereof,
is strictly prohibited.

Parts of this software are licensed and used in software developed by Lummetry.AI.
Any software proprietary to Knowledge Investment Group SRL is covered by Romanian and  Foreign Patents,
patents in process, and are protected by trade secret or copyright law.

Dissemination of this information or reproduction of this material is strictly forbidden unless prior
written permission from the author


@copyright: Lummetry.AI
@author: Lummetry.AI
@project: 
@description:
@created on: Tue Aug  8 16:56:41 2023
@created by: damia
"""
from time import sleep

if __name__ == '__main__':
  cnt = 1
  while True:
    print("**** PING {} from {}".format(cnt, __file__), flush=True)
    cnt += 1
    sleep(3600)
