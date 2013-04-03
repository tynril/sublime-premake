Sublime Text Premake Plugin
===========================

This plugin enables the usage of [Premake](http://industriousone.com/premake) from within Sublime Text, and
provides a portable multi-files build system using it.

Installation
------------

To install the Premake plugin, you can:

 * Use `git` to clone this repository inside your Sublime Text installation packages directory;
 * Download an archive of this repository and uncompress it in your Sublime Text installation package directory.

For this plugin to work, you also need to have `premake4` and `make` installed and available in your `PATH`.

Getting Started
---------------

In order to use the Premake plugin, you must:

 * __Have a Sublime Text project opened__  
   The Premake plugin uses your project settings file to retrieve and store its settings, such as the premake
   build file path.
 * __Have a premake build file__  
   This plugin is meant to _use_ your premake build file, not to _generate_ it. By default, this file is named
   `premake4.lua` and is to be stored in the root directory of your project. If you want to, you can change
   this behavior by setting a `premake_file` setting in your project settings file, and this path will be used
   instead.

Usage
-----

You can use the Premake plugin to:

 * __Generate your build files__  
   To do that, simply execute the `Premake: Generate` command. The `premake4` utility is run to generate GNU Makefiles.
 * __Clean the build files__  
   Using the `Premake: Clean` command.
 * __Build your project__  
   Select the `Premake` build system (in `Tools > Build System`), and build your project like you would normally do,
   using the `Build: Build` command (or `Ctrl+B`/`⌘+B`). This will use the generated makefiles to build your whole
   project. If no configuration was specified, it will build the default configuration.
 * __Change the build configuration__  
   If you defined multiple build configurations (like `Debug` and `Release`), you can use the `Premake: Select
   Configuration` command to choose which configuration the build system should build. You can also edit the
   `premake_configuration` setting in your project file, if you prefer.
 * __Run your project__  
   Once the `Premake` build system selected, you can use the `Build: Run` (or `Ctrl+Shift+B`/`⌘+Shift+B`) command to run
   your project. If there's more than one runnable target in it, you will be prompted to choose which one you want to
   run. Your choice will be memorized in the `premake_run_target` setting of your project file. You can change it here,
   or use the `Premake: Select Run Target` command to make a new choice.

License
-------

This plugin is provided under the [MIT Open Source License](http://opensource.org/licenses/MIT). That means you're free
to use it for anything as long as you keep my name and the copyright notice with it. Also, I'm not responsible for
anything you'll do with this plugin.

    Copyright (c) 2012 Samuel Loretan (tynril at gmail dot com)
    
    Permission is hereby granted, free of charge, to any person obtaining a copy
    of this software and associated documentation files (the "Software"), to deal
    in the Software without restriction, including without limitation the rights
    to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the Software is
    furnished to do so, subject to the following conditions:
    
    The above copyright notice and this permission notice shall be included in
    all copies or substantial portions of the Software.
    
    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
    SOFTWARE.
