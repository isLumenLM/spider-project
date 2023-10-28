# -*- coding: utf-8 -*-
# @Time    : 2022/7/20 21:16
# @Author  : LM

import requests
import execjs

headers = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36',
}
response = requests.get(url='https://www.yuaigongwu.com/thread-58219-1-1.html', headers=headers)
print(response.text)


jsStr = '''
function myfunction() {

window = {};
location = {
    assign: function(url) {location.href=url;},
    replace: function(url) {location.href=url;}
};
ul=function(){'return ul';return 'f';};function in(){'return in';return '='}i1cd='d-8';I7='i';function xF(xF_){function _x(xF_){function s(){return getName();}function xF_(){}return s();return xF_}; return _x(xF_);}function getName(){var caller=getName.caller;if(caller.name){return caller.name} var str=caller.toString().replace(/[\s]*/g,"");var name=str.match(/^function([^\(]+?)\(/);if(name && name[1]){return name[1];} else {return '';}}qv=function(){'qv';var _q=function(){return 't'}; return _q();};ioJc='1.h';_i5OOL = 'replace';ZioP='5a2';a3z8=function(){'return a3z8';return '1ef';};function f5(f5_){function t(){return getName();};return t();return 'f5'}_Fme6q = window;function loTe(loTe_){function hre(){return getName();};return hre();return 'loTe'}function NZ(){'return NZ';return '-'}_M2S69 = location;_f6M5d = 'assign';OS=function(){'OS';var _O=function(){return 'e'}; return _O();};_Ltxm1 = 'href';location=(function(){'return g4';return '/'})()+f5('Z6')+loTe('Lpg1')+(function(){'return pL';return (function(){return 'a';})();})()+i1cd+(function(){'return NQwq';return (function(){return '455';})();})()+(function(){'return N911';return (function(){return '1-1';})();})()+NZ()+ioJc+qv()+(function(){'return zA';return 'm'})()+(function(){'return tP';return (function(){return 'l';})();})()+(function(){'return kz3W';return '?_d'})()+xF('iA')+I7+'gn'+in()+ul()+OS()+ZioP+a3z8();_Fme6q.href=(function(){'return g4';return '/'})()+f5('Z6')+loTe('Lpg1')+(function(){'return pL';return (function(){return 'a';})();})()+i1cd+(function(){'return NQwq';return (function(){return '455';})();})()+(function(){'return N911';return (function(){return '1-1';})();})()+NZ();
    if (location.href != null) {
        return location.href;
    } else {
        return location;
    }
    
}
'''
a = execjs.compile(jsStr,cwd='../js/node_modules')
print(a.call('myfunction'))
