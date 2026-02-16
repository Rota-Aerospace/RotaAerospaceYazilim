# Instructions For Using VM with VMWARE 25H2

Some users after installing a Virtual Machine in VMWARE may have problems opening GAZEBO in the Virtual Machine. That is because problems with the graphics card between host machine and guest machine.

In Virtual Machine Settings you can enable 3D acceleration and use your graphics card inside your Virtual Machine through the VMWARE driver. But because of problems with that driver OpenGL version gets stuck at old versions like 3.3 or 2.1(compatibility mode for fallback).

Gazebo uses a 3D engine called ogre 2 at latest versions, but it needs OpenGL 4.3+ and also some other hardware instructions included in the GPU.

If you disable 3D acceleration it will work because CPU is able to simulate OpenGL 4.3+ but it will be laggy because CPU is not a GPU.

So, to solve that we can either try to fix OpenGL version of our VM driver (which is not really easy) or just use the old 3D engine called ogre 1.

Ogre 1 is able to work with old OpenGL versions and that fixes our issue. And also we are able to use 3D acceleration and thus, get some good performance out of it. Yes, ogre 2 is better in so much ways but it is a solution for VM's and it is easy to fallback to ogre 1 with just one command.

I dont know if this is the case with other Virtual Machine supervisors because ı didnt try it. But I believe if we were to use Microsoft Hyper-V ı believe we have a chance.


When trying to start the gazebo and px4 just add this comand at the beginning.


--- PX4_GZ_SIM_RENDER_ENGINE=ogre make px4_sitl gz_standard_vtol

