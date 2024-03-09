def getBandByStartFrequency( startFrequency:float , width:float , step=6.25 ) :
    steps = int(float(width) / step )
    band = [startFrequency]
    for i in range( steps - 1  ) :
        band.append( band[-1] + step/10 )

    central = int(len(band) / 2 - 1)
    cf = band[central + 1]

    return {
        'band' : band ,
        'cf' : cf,
        'start' : band[0] ,
        'end' : band[-1]
    } 



def getBandByCf(cf:float , width:float ,step:float=6.25) :

    totalSteps = int(float(width) / float(step))
    totalStepsForward = int((totalSteps/2)) - 1
    totalStepsBackward = int(totalSteps / 2)
    fullBand= [cf]
    for i in range(int(totalStepsForward)) :
        freq = fullBand[-1]
        fullBand.append((freq + step/10))

    for i in range(int(totalStepsBackward)) :
        freq = fullBand[0]
        fullBand.insert( 0 , freq - step/10 )
    
    return fullBand


if __name__ == '__main__':
    pass


