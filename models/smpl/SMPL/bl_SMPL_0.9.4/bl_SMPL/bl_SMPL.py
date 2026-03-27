'''
Script Authors: Thomas Nguyen (Thomas.Nguyen@bodylabs.com) in collaboration with
                Naureen Mahmood and the Max Planck Gesellschaft.
--------------
SMPL and Body Labs SMPL is a product of the Max Planck Gesellschaft and Body Labs. All rights reserved.
This software is provided for research purposes only.
More information about SMPL is available here http://smpl.is.tue.mpg.
For comments or questions, please email us at: smpl@tuebingen.mpg.de
'''

VERSION = '0.9.4'
SMPL_VERSION = '1.0.2'

'''
Current Maya versions supported:
--------------------------
Mac OSX: Maya 2014+
Windows: Maya 2014+

Dependencies:
------------
1)  The file Joints_mat_v*.pkl should be included in the same folder as this script.

2)  Numpy is required for running SMPL. Numpy is a python module that
    can be installed following the instructions given here:
    http://docs.scipy.org/doc/numpy/user/install.html

    or here:
    http://blog.animateshmanimate.com/post/115538511578/python-numpy-and-maya-osx-and-windows

    Please make sure you have numpy installed on your computer and accessible through Maya's python.
    We are working towards removing this dependency.


Installation Steps:
------------------
1)  Make sure no other copies of bl_SMPL will load with Maya

2)  Copy this 'bl_SMPL' folder into your Maya Scripts folder. eg:
    windows:     "<drive:>/Users/<user>/Documents/maya/scripts"
    OSX:        "/Library/Preferences/Autodesk/maya/<version>/scripts"

3) Update the location of the SMPL files in the following lines:
'''
from os.path import expanduser
SMPL_dir = expanduser('~/Documents/maya/plugins/')

'''
4)  Inside Maya, go to Window >> Settings/Preferences >> Plug-in Manager
Locate the bl_SMPL.py script and check 'Loaded'


Use:
---
1)  Run the script and a UI will load. Use that UI to load the SMPL rig.

2)  Pose and adjust the model as you would normally, and the rest should take care of itself.
'''

import sys
import maya.cmds as mc
import maya.mel as mel
import cPickle as pickle
from os.path import exists, dirname, abspath
from functools import partial

try:
    import numpy as np
except:
    python_version = sys.version_info
    sys.path.append( '/usr/local/lib/python%d.%d/site-packages/' % (python_version.major, python_version.minor) )
    import numpy as np

# Create a Maya Global var independant of the UI to set the scriptJob state for the length of the Maya session.
mel.eval('global string $gs_SMPL_SJ = "";')

class bl_SMPL():
    def __init__( self ):

        self.win = 'SMPL_win'
        self.winTitle = 'Body Labs SMPL'
        self.target = None
        self.blendShapeNode = None
        self.skinCluster = None

        ## Dictionary for matching joint index to name
        self.j_names = {
            0:  'Pelvis',
            1:  'L_Hip',        4:  'L_Knee',            7:  'L_Ankle',           10: 'L_Foot',
            2:  'R_Hip',        5:  'R_Knee',            8:  'R_Ankle',           11: 'R_Foot',
            3:  'Spine1',       6:  'Spine2',            9:  'Spine3',            12: 'Neck',            15: 'Head',
            13: 'L_Collar',     16: 'L_Shoulder',       18: 'L_Elbow',            20: 'L_Wrist',         22: 'L_Hand',
            14: 'R_Collar',     17: 'R_Shoulder',       19: 'R_Elbow',            21: 'R_Wrist',         23: 'R_Hand',
        }

        self.shape_dict = {
            'Shape000': 'Height',
            'Shape001': 'Weight',
            'Shape002': 'Inseam_and_Reach',
            'Shape003': 'Hip_Height',
            'Shape004': 'Neck_Length',
            'Shape005': 'Subtle_Weight',
            'Shape006': 'Torso_vs_Limbs',
            'Shape007': 'Chest_Height',
            'Shape008': 'Fitness',
            'Shape009': 'Vertical_Weight'
        }

        # self.shapesInReverse = ['Shape000', 'Shape001', 'Shape002', 'Shape003', 'Shape004', 'Shape006', 'Shape007', 'Shape008']

        self.jointsCB = True # default value for auto-recompute skeleton checkbox
        self.shapesCB = True # default value for auto-recompute shapes checkbox

        self.selChanged_SJ_ID = 0 # holder for 'selectionChanged' scriptjob ID
        self.attChanged_SJ_ID = 0 # holder for 'attributeChange' scriptjob IDs
        self.uiDeleted_SJ_ID = 0 # holder for 'uiDeleted' scriptjob ID
        # self.SMPL_dir = dirname( abspath("__file__") )
        self.SMPL_dir = SMPL_dir
        self.SMPL_JM_file = '%s/joints_mat_v%s.pkl' % ( self.SMPL_dir, SMPL_VERSION )
        if not exists( self.SMPL_JM_file ):
            self.myPrint("<font color=red>The Joints_mat_v%s.pkl file was not found. \n Please make sure Joints_mat_v%s.pkl is in the same scripts folder. \n ie: %s" % ( SMPL_VERSION, SMPL_VERSION, SMPL_dir ), 'topCenter', 1, 10000)
            return

    # SCRIPTJOB HANDLING
    def start_SMPL_SJ( self, *args ):
        '''
        Enable SMPL scriptJobs to auto shape correct on the
        events that selected joint rotations have changed.
        '''
        self.selChanged_SJ_ID = mc.scriptJob( ro=False, cu=True, e=['SelectionChanged', partial( self.selectionHandling ) ] )

    def kill_SMPL_SJ( self, selChange=False, attChange=False ):
        '''
        Disable selection changed scriptjob.
        '''
        if selChange and self.selChanged_SJ_ID > 0:
            sjID = self.selChanged_SJ_ID
            self.selChanged_SJ_ID = 0
            mc.scriptJob( kill=sjID, force=True )

        if attChange and self.attChanged_SJ_ID > 0:
            sjID = self.attChanged_SJ_ID
            self.attChanged_SJ_ID = 0
            mc.scriptJob( kill=sjID, force=True )


    def selectionHandling( self ):
        '''
        Handle new selections.
        '''
        if mc.ls( sl=True, type='joint' ):
            self.attChanged_SJ_ID = mc.scriptJob( ac=[ mc.ls( sl=True, type='joint' )[0] + '.rotate', partial( self.attributeChanged ) ], runOnce=True )


    def attributeChanged( self ):

        # let the user know if autokey is not enabled
        autoKey = mc.autoKeyframe( query=True, state=True )
        # if not autoKey:
        #     self.myPrint("<font color=yellow>Autokey has been disabled. \n Please turn autokey back ON if you want keep your animation changes!", 'topCenter', 1, 4000)

        # deselect everything before calling reshape to avoid going into a attribute change scriptjob loop
        sel = mc.ls( sl=True )
        mc.select( clear=True )

        self.reshape()

        # reselect what we deselected
        mc.select( sel )


    #######################
    #
    # UI COMMANDS
    #
    #######################

    def getTargetBody( self ):
        '''
        Returns an SMPL body name via a prioritized systematic search.
        '''
        self.target = ''
        if mc.ls( sl=True ):
            if mc.filterExpand( sm=12 ):
                if mc.listConnections( mc.listRelatives( children=True )[0], type='skinCluster' ):
                    self.target =  mc.filterExpand( sm=12 )[0]
            else:
                if mc.listConnections( type='skinCluster' ):
                    self.target = mc.listConnections( mc.listConnections( type='skinCluster' )[0], type='mesh' )[0]
                else:
                    if mc.ls( type='skinCluster' ):
                        self.target = mc.listConnections( ( mc.ls( type='skinCluster' )[0] ), type='mesh' )[0]

        else:
            if mc.ls( type='skinCluster' ):
                self.target = mc.listConnections( ( mc.ls( type='skinCluster' )[0] ), type='mesh' )[0]

        self.skinCluster = mc.listConnections( mc.listRelatives(self.target, children=True )[0], type='skinCluster' )[0]

        return self.target


    def importSMLP( self, *args ):
        '''
        Loads a File Dialogue Box that allows the user to import an SMPL rig.
        '''
        filters = "All Files (*.*);;FBX (*.fbx);;Maya ASCII (*.ma);;Maya Binary (*.mb)"
        sceneFile = mc.fileDialog2( fileMode=1,
                                    startingDirectory= '%s/sample_scenes' % self.SMPL_dir,
                                    caption='Import SMPL Body',
                                    fileFilter=filters,
                                    okCaption='Import',
                                    dialogStyle=2
                                    )
        if sceneFile:
            mc.file( sceneFile, open=True, force=True)

        if mc.objExists( '*Pose206' ):
            self.target = self.getTargetBody()

            rescale = mc.checkBox( self.convertUnitsCB, query=True, value=True )
            hideRoot = mc.checkBox( self.hideRootCB, query=True, value=True )
            setRange = mc.checkBox( self.setRangeCB, query=True, value=True )

            if rescale or hideRoot:
                targetJoints = mc.listConnections( mc.listConnections(mc.listRelatives( self.target, type='shape')[0], type='skinCluster' )[0], type='joint' )
                for j in targetJoints:
                    if rescale:
                        mc.setAttr( j + '.scale', 100, 100, 100, type="double3")
                        mc.setAttr( j + '.radius', 0.01)

                    if hideRoot and 'root' in j:
                        mc.setAttr( j + ".drawStyle", 2 )

                    if setRange and 'Pelvis' in j:
                        if mc.objExists( j + '_rotateX' ):
                            frameCount = mc.keyframe( j + '_rotateX' , query=True, keyframeCount=True ) - 1
                            mc.playbackOptions( min=0, max=frameCount, animationEndTime=frameCount )

            mc.select( self.target )
            mel.eval( 'FrameSelected;' )
            mc.select( clear=True )
            self.loadUI()


    def setTarget( self, *args ):
        '''
        Refresh the UI with the user's selection.
        '''
        # maybe do more than this...
        self.loadUI()


    def toggleBindPose( self, toggleBP, *args ):
        if toggleBP:
            # disable autokey so that we dont key the bind pose
            autoKey = mc.autoKeyframe( query=True, state=True )
            mc.autoKeyframe( state=False )
            if not autoKey:
                self.myPrint("<font color=white>Autokey has been disabled. \n Please turn autokey back ON when you're ready to animate.", 'topCenter', 1, 4000)

            targetJoints = mc.listConnections( mc.listConnections(mc.listRelatives( self.target, type='shape')[0], type='skinCluster' )[0], type='joint' )

            for j in targetJoints:
                if 'root' not in j and 'Pelvis' not in j:
                    mc.setAttr( j + '.rotate', 0, 0, 0, type="double3")

            for idx in range(207):
                mc.setAttr( self.blendShapeNode + '.Pose%03d' % (idx), 0 )

            mc.button( self.bindPoseButton, edit=True, command=partial( self.toggleBindPose, False ) )
        else:
            # Refresh the viewport to reset the pose
            mc.currentTime( mc.currentTime( query=True ) )

            mc.button( self.bindPoseButton, edit=True, command=partial( self.toggleBindPose, True ) )


    def resetShape( self, *args ):
        '''
        Reset the Shape to Starting Values
        '''
        for i, bsSlider in enumerate( self.bsSliderList ):
            mc.floatSliderGrp( bsSlider, edit=True, value=self.bsSliderValues[i] )
            bs = mc.floatSliderGrp( bsSlider, query=True, annotation=True )
            mc.setAttr( self.blendShapeNode + '.' + bs, self.bsSliderValues[i] )

        # Reset joints
        self.reJoints()


    def bsUpdateVal( self, bsSlider, bs, *args ):
        bsVal = mc.floatSliderGrp( bsSlider, query=True, value=True )
        if not bs.startswith('my_'):
            bsVal = -bsVal
        mc.setAttr( self.blendShapeNode + '.' + bs, bsVal )

    def getVtxPos( self, shapeNode ) :
        '''
        Get the vertices of a maya mesh 'shapeNode'
        :param  shapeNode: name of maya mesh
        :return vertices of the maya mesh object
        '''
        vtxWorldPosition = []
        vtxIndexList = mc.getAttr( shapeNode+".vrts", multiIndices=True )
        for i in vtxIndexList :
            curPointPosition = mc.xform( str(shapeNode)+".pnts["+str(i)+"]", query=True, translation=True, worldSpace=True )    # [1.1269192869360154, 4.5408735275268555, 1.3387055339628269]
            vtxWorldPosition.append( curPointPosition )
        return vtxWorldPosition


    def autoReJoints( self, bsSlider, bs, *args ):
        '''
        Recalculate the joint positions via the weight sliders.
        '''
        bsVal = mc.floatSliderGrp( bsSlider, query=True, value=True )
        if not bs.startswith('my_'):
            bsVal = -bsVal
        mc.setAttr( self.blendShapeNode + '.' + bs, bsVal )
        if mc.checkBox( self.reJointsCheckbox, query=True, value=True ):
            self.reJoints()


    def reJoints( self, *args ):
        '''
        Recalculate the joint positions.
        '''
        # Turn Off Autokey so that we don't key the bind pose
        autoKey = mc.autoKeyframe( query=True, state=True )
        mc.autoKeyframe( state=False )

        maya_mesh = mc.listRelatives( self.target, type='shape')[0]
        targetJoints = mc.listConnections( mc.listConnections(mc.listRelatives( self.target, type='shape')[0], type='skinCluster' )[0], type='joint' )

        for j in targetJoints:
            mc.setAttr( j + '.rotate', 0, 0, 0, type="double3")
            if 'root' in j:
                rootBone = j
                bonePrefix  = rootBone.replace('_root', '')

        ## Get new joint heirarchy
        with open (self.SMPL_JM_file) as f: joints_mat = pickle.load(f)

        ## Get mesh vertices
        mesh_verts = self.getVtxPos( maya_mesh )
        gender = 'male' if maya_mesh[0]=='m' else 'female'

        ## Get new joints
        subject_j = joints_mat[gender].dot( np.asarray( mesh_verts ) )

        ## Lock skinning and set new joint locations
        mc.skinCluster( maya_mesh, edit=True, moveJointsMode=True )
        for j_idx, j_name in self.j_names.iteritems():
            currentBone = '%s_%s' % ( bonePrefix, j_name )
            mc.move( subject_j[j_idx][0], subject_j[j_idx][1], subject_j[j_idx][2], currentBone )
        mc.skinCluster( maya_mesh, edit=True, moveJointsMode=False )

        # Reset Autokey
        mc.autoKeyframe( state=autoKey )

        # Refresh the viewport to reset the pose
        mc.currentTime( mc.currentTime( query=True ) )


    def reshapeAlwaysOnCB( self, *args ):
        '''
        Reshape always on checkbox command
        '''
        if mc.checkBox( self.reshapeAlwaysOnCheckbox, query=True, value=True ):
            mel.eval('global string $gs_SMPL_SJ = "1";')

            # kill the uiDelete scriptjob that disables scriptjobs when the UI is closed
            if self.uiDeleted_SJ_ID > 0:
                mc.scriptJob( kill=self.uiDeleted_SJ_ID, force=True )
                self.uiDeleted_SJ_ID = 0

        else:
            mel.eval('global string $gs_SMPL_SJ = "";')
            if self.uiDeleted_SJ_ID == 0:
                self.uiDeleted_SJ_ID = mc.scriptJob( ro=0, cu=1, uiDeleted=[ self.win , partial( self.kill_SMPL_SJ, True, True ) ] )


    def reshape( self, use_range=False, *args ):
        '''
        Re-apply the corrective blendShape values to the input frame range.
        '''

        maya_mesh = mc.listRelatives( self.target, type='shape')[0]

        lbs_cluster = mc.listConnections( maya_mesh, type='skinCluster' )[0]
        rootBone    = [b for b in mc.listConnections( lbs_cluster, type='joint') if 'root' in b ][0]
        bonePrefix  = rootBone.replace('_root','')

        if use_range:
            f1 = int( mc.intFieldGrp( self.framesField, query=True, value1=True ))
            f2 = int( mc.intFieldGrp( self.framesField, query=True, value2=True ))
            frame_range = [ f1, f2+1 ]
        else:
            currentTime = int( mc.currentTime( query=True ))
            frame_range = [ currentTime, currentTime+1 ]

        for frame in range( frame_range[0], frame_range[-1] ):
            mc.currentTime( frame )

            ## Reset poseblends for all joints excluding pelvis (there are no blendShapes for pelvis)
            for jidx, j_name in self.j_names.iteritems() :
                bone = '%s_%s' % (bonePrefix, j_name )
                if jidx > 0 and (frame_range[-1] - frame_range[0]) > 0:
                    ## Get original 4x4 maya rotation matrix from bone
                    xf = mc.xform( bone, query=True, matrix=True )
                    dif_l = xf[0]-1, xf[4], xf[8], xf[1], xf[5]-1, xf[9], xf[2], xf[6], xf[10]-1
                    for mi, rot_element in enumerate( dif_l ):
                        bidx = (9*(jidx-1)) + mi
                        mc.setAttr( '%s.Pose%03d' % ( self.blendShapeNode, bidx ), rot_element )
                        # Set new key
                        mc.setKeyframe( '%s.Pose%03d' % ( self.blendShapeNode, bidx ), breakdown=False, controlPoints=False, shape=False )


    def checkBoxUpdate( self, checkbox, *args ):
        '''
        Toggle the Recompute button enablility.
        '''
        if checkbox == 'joint':
            mc.button( self.reJointsButton, edit=True, enable=self.jointsCB )
            self.jointsCB = not self.jointsCB
            if self.jointsCB:
                self.reJoints()
        if checkbox == 'shape':
            if mc.checkBox( self.reshapeCheckbox, query=True, value=True ):
                self.start_SMPL_SJ()
                mc.checkBox( self.reshapeAlwaysOnCheckbox, edit=True, enable=True )
                if mc.checkBox( self.reshapeAlwaysOnCheckbox, query=True, value=True ):
                    mel.eval('global string $gs_SMPL_SJ = "1";')
                    self.start_SMPL_SJ()

            else:
                mc.checkBox( self.reshapeAlwaysOnCheckbox, edit=True, enable=False )
                mel.eval('global string $gs_SMPL_SJ = "";')
                self.kill_SMPL_SJ( selChange=True, attChange=True )

            self.shapesCB = not self.shapesCB


    def myPrint( self, note, placement, f, fst):
        '''
        An easy way to print messages on the screen that bypasses any user restrictions.
        '''
        inViewMessage = mc.optionVar(q='inViewMessageEnable')
        inViewAssist = mc.optionVar(q='inViewMessageEnable')
        mc.optionVar( iv=('inViewMessageEnable', 1) )
        mc.optionVar( iv=('inViewMessageAssistEnable', 1) )

        mc.inViewMessage(amg=note, pos=placement, bkc=0x008D998D, fade=f, fadeStayTime=fst )

        mc.optionVar(iv=('inViewMessageEnable', inViewMessage))
        mc.optionVar( iv=('inViewMessageAssistEnable', inViewAssist) )

    # UI
    def loadUI( self, resize=True ):
        '''
        Construct the SMPL controller UI.
        '''
        # Maya global value for auto-recompute shapes always on checkbox
        self.gs_SMPL_SJ = bool( mel.eval('$tempVal = $gs_SMPL_SJ;') )


        if( mc.window( self.win, exists=True ) ):
            mc.deleteUI( self.win, window=True )

        mc.window( self.win, title=self.winTitle)
        logoCL = mc.columnLayout( columnAttach=('both', 0), rowSpacing=1, adjustableColumn=True )
        mc.iconTextButton( parent=logoCL, style='iconOnly', image1=self.SMPL_dir + '/bl_logo.png')

        if mc.objExists( '*Pose206' ):

            self.target = self.getTargetBody()

            self.blendShapeNode = mc.listConnections( mc.listConnections( mc.listRelatives( self.target, type='shape')[0], type='objectSet' ), type='blendShape' )[0]

            mainFormLayout = mc.formLayout(numberOfDivisions=3)

            # Target command frame
            targetFrameLayout = mc.frameLayout( parent=mainFormLayout,
                                                label='Current Target:  %s' % (self.target),
                                                backgroundColor=(0.0, 0.5, 0.5),
                                                borderVisible=False,
                                                collapsable=True,
                                                collapseCommand=partial( mc.window,self.win, edit=True, height=100 )
                                                )
            targetRowLayout = mc.rowLayout( parent=targetFrameLayout, numberOfColumns=2, columnWidth2=(180, 180), columnAttach=[(1, 'both', 2), (2, 'both', 2)] )
            # newShapeColumn = mc.columnLayout( parent=targetFrameLayout, columnAttach=('both', 50), rowSpacing=10, adjustableColumn=True )

            targetButton = mc.button( parent=targetRowLayout, label='Set Selected as Target', height=30, command=self.setTarget )
            self.bindPoseButton = mc.button( parent=targetRowLayout, label='Toggle Bind Pose ON/OFF', height=30, command=partial( self.toggleBindPose, True ) )

            # Weight sliders frame
            shapesFrameLayout = mc.frameLayout( parent=mainFormLayout,
                                                label='Weight Sliders',
                                                borderVisible=False,
                                                collapsable=True,
                                                collapseCommand=partial( mc.window,self.win, edit=True, height=100 )
                                                )
            resetShapesButton = mc.button( parent=shapesFrameLayout, label='Reset to Starting Shape', height=20, command=self.resetShape )
            # importShapeButton = mc.button( parent=shapesFrameLayout, label='Import/Add New Shape to Rig', height=20, command=(self.addShape))

            shapeScrollLayout = mc.scrollLayout( parent=shapesFrameLayout, height=260, horizontalScrollBarThickness=16, verticalScrollBarThickness=16 )

            # for sliders
            shapeRowColumn = mc.rowColumnLayout( parent=shapeScrollLayout, numberOfColumns=2, columnWidth=[(1, 104), (2, 240)], columnSpacing=[2,5] )

            # for re-compute buttons
            autoFrameLayout = mc.frameLayout( parent=mainFormLayout, label='Recompute Options', borderVisible=False, collapsable=True)
            shapeColumn = mc.columnLayout( parent=autoFrameLayout, columnAttach=('both', 0), rowSpacing=10, adjustableColumn=True )


            # UPDATE UI WITH BODY INFO AND WEIGHT SLIDERS
            blendShapes = mc.listConnections( self.blendShapeNode, type='mesh')
            blendShapes = [] if blendShapes==None else blendShapes

            self.bsSliderList = []
            self.bsSliderValues = []

            for shape in reversed(blendShapes):
                if shape.startswith('my'):
                    bs = shape
                    bsVal = mc.getAttr( '%s_blendshapes.%s' % (self.target, bs) )

                    # Save this value for the reset function
                    self.bsSliderValues.append( bsVal )

                    mc.text( parent=shapeRowColumn, label=bs, align='right' )
                    bsSlider = mc.floatSliderGrp( parent=shapeRowColumn, annotation=bs, width=200, field=True, precision=1, minValue=-0, maxValue=1, fieldMinValue=-5.0, fieldMaxValue=5.0, value=bsVal )
                    self.bsSliderList.append( bsSlider )
                    mc.floatSliderGrp( bsSlider, edit=True, dragCommand=partial( self.bsUpdateVal, bsSlider, bs ), changeCommand=partial( self.autoReJoints, bsSlider, bs ) )

            for idx in range(10):
                bs = 'Shape%03d' % (idx)
                bsVal = mc.getAttr( self.target + '_blendshapes.' + bs )

                # Save this value for the reset function
                self.bsSliderValues.append( bsVal )

                mc.text( parent=shapeRowColumn, label=self.shape_dict[bs], align='right' )
                bsSlider = mc.floatSliderGrp( parent=shapeRowColumn, annotation=bs, width=200, field=True, precision=3, minValue=-4.0, maxValue=4.0, fieldMinValue=-5.0, fieldMaxValue=5.0, value=-bsVal )

                self.bsSliderList.append( bsSlider )
                mc.floatSliderGrp( bsSlider, edit=True, dragCommand=partial( self.bsUpdateVal, bsSlider, bs ), changeCommand=partial( self.autoReJoints, bsSlider, bs ) )


            # Compute joints
            mc.rowLayout( parent=shapeColumn, numberOfColumns=2, columnWidth2=(179, 181), columnAttach=[(1, 'both', 8), (2, 'both', 2)], rowAttach=(1, 'top', 6))
            self.reJointsCheckbox = mc.checkBox( label='Auto-Recompute \n Skeleton', align='right', value=self.jointsCB, changeCommand=partial( self.checkBoxUpdate, 'joint' ) )
            self.reJointsButton = mc.button( label = 'Recompute Skeleton', enable=not self.jointsCB, width = 170, height=30, command=self.reJoints )
            mc.setParent( '..' )

            mc.separator( height=2, style='in')

            # Compute shapes
            self.reshapeCheckbox = mc.checkBox( label='Auto-Recompute Corrective Shapes for Current Frame', align='right', value=self.shapesCB, changeCommand=partial( self.checkBoxUpdate, 'shape' ) )
            self.reshapeAlwaysOnCheckbox = mc.checkBox( label='Keep Auto-Recompute ON Even When UI is OFF', align='right', value=self.gs_SMPL_SJ, changeCommand=self.reshapeAlwaysOnCB )

            # mc.rowLayout( numberOfColumns=1, columnAttach=[(1, 'left', 192)] )
            # mc.setParent( '..' )

            mc.rowLayout( parent=shapeColumn, numberOfColumns=2, columnWidth2=(179, 181), columnAttach=[(1, 'both', 8), (2, 'both', 2)] )
            self.reshapeButton = mc.button( label = 'Recompute Shape \n for the Side Frame Range \n (Values Will be Keyed)', width = 170, height=50, command=partial( self.reshape, True ) )
            self.framesField = mc.intFieldGrp( numberOfFields=2, value1=0, value2=10 )
            mc.setParent( '..' )

            mc.separator( height=2, style='in')

            endColumn = mc.columnLayout( parent=mainFormLayout, columnAttach=('both', 0), rowSpacing=10, adjustableColumn=True )
            mc.text( parent=endColumn, label=( 'v.' + VERSION ), width=360, align='center' )


            # Edit form layout configuration
            mc.formLayout( mainFormLayout, edit=True,
                            attachForm=[(targetFrameLayout, 'left', 5), (targetFrameLayout, 'right', 5), (targetFrameLayout, 'top', 10), (autoFrameLayout, 'left', 5), (autoFrameLayout, 'bottom', 24), (autoFrameLayout, 'right', 5), (shapesFrameLayout, 'left', 5), (shapesFrameLayout, 'right', 5), (endColumn, 'bottom', 5) ],
                            attachControl=[(shapesFrameLayout, 'top', 5, targetFrameLayout), (shapesFrameLayout, 'bottom', 5, autoFrameLayout)],
                            attachNone=(autoFrameLayout, 'top') )

            if resize:
                mc.window( self.win, edit=True, width=350, height=400 )


        else: # load importer
            # importSMLP()

            mc.columnLayout( columnAttach=('both', 0), rowSpacing=10, adjustableColumn=True )
            mc.text( label='No SMPL Rig Found; Please Import an SMPL Rig.', height=30, backgroundColor=(0.0, 1.0, 1.0) )
            mc.setParent('..')

            mc.columnLayout( columnAttach=('both', 10), rowSpacing=10, adjustableColumn=True )
            self.importButton = mc.button( label='IMPORT', width=80 )
            self.convertUnitsCB = mc.checkBox( label='Scale to Real World Units', align='center', value=True )
            self.hideRootCB = mc.checkBox( label='Hide Root Joint', align='center', value=True )
            self.setRangeCB = mc.checkBox( label='Set Timeline to Animation Range', align='center', value=True )
            mc.setParent('..')

            # Callback
            mc.button( self.importButton, edit=True, command=partial( self.importSMLP, self.convertUnitsCB, self.hideRootCB, self.setRangeCB ) )

            mc.window( self.win, edit=True, width=300, height=180 )

        # SHOW UI
        mc.showWindow( self.win )

        # Scriptjobs
        '''
        We'll use scriptjobs to handle automatic shape corrections
        until we implement a better Set Driven Keys setup.
        '''

        # kill any old scriptjobs
        sj = mc.scriptJob( lj=True )
        shSJ = []
        for j in sj:
            if 'functools' in j:
                jtoke = j.split(':')
                shSJ.append(int(jtoke[0]))
                if shSJ:
                    for k in shSJ:
                        mc.scriptJob( kill=k, force=True )
                del shSJ[:]

        # start scriptjob to kill scriptjobs when the UI is closed
        if not bool( mel.eval('$tempVal = $gs_SMPL_SJ;') ):
            self.uiDeleted_SJ_ID = mc.scriptJob( ro=0, cu=1, uiDeleted=[ self.win , partial( self.kill_SMPL_SJ, True, True ) ] )

        if self.shapesCB:
            self.start_SMPL_SJ()

def loadUI():
    bl_SMPL.loadUI()

bl_SMPL = bl_SMPL()
bl_SMPL.loadUI()
