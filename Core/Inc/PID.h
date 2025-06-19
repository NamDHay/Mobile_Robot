/*
 * pid.h
 *
 *  Created on: Oct 4, 2024
 *      Author: warlord
 */

#ifndef _PID_H_
#define _PID_H_

#include "main.h"
#include "math.h"
#include <stdlib.h>
#include <stdint.h>


typedef struct PID_Param{
	//---------Input Parameters-----------//
    float e;
    float e_Pre;
    float deltaT;
	//---------Propotion Parameters-------//
    float kP;
    float uP;
	//---------Intergral Parameters-------//
    float kI;
    float uI;
    float kB;// gain value to control anti-windup of Intergral
	//---------Derivative Parameters------//
    float kD;
    float uD;
    float uD_Fil;
    float uD_FilPre;
    float alpha;
	//---------Sum Parameters-------------//
    float u;
    float uHat; // the result of 'u' value after passing "Saturation" stage
    float u_AboveLimit;
    float u_BelowLimit;

}PID_Param;

float PID_Calculate(PID_Param *pid, float setPoint, float currentValue);
void PID_SetParameters(PID_Param *pid, float _kP, float _kI, float _kD, float _alpha, float _deltaT);
void PID_SetSaturate(PID_Param *pid, float uAbove, float uBelow);


#endif /* INC_PID_H_ */
