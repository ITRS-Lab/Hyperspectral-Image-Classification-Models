import torch
import numpy as np
from torch.autograd import Variable
min_var_est = 1e-8

def guassian_kernel(source, target, kernel_mul=2.0, kernel_num=5, fix_sigma=None):
    n_samples = int(source.size()[0]) + int(target.size()[0])
    total = torch.cat([source, target], dim = 0)
    total0 = total.unsqueeze(0).expand(int(total.size(0)), int(total.size(0)), int(total.size(1)))
    total1 = total.unsqueeze(1).expand(int(total.size(0)), int(total.size(0)), int(total.size(1)))
    
    L2_distance = ((total0 - total1)**2).sum(2)
    if fix_sigma:
        bandwidth = fix_sigma
    else:
        bandwidth = torch.sum(L2_distance.data) / (n_samples**2 - n_samples)
    
    bandwidth /= kernel_mul ** (kernel_num // 2)
    bandwidth_list = [bandwidth * (kernel_mul**i) for i in range(kernel_num)]
    kernel_val = [torch.exp(-L2_distance / bandwidth_temp) for bandwidth_temp in bandwidth_list]
    return sum(kernel_val)
    

def conditional_mmd(source, target, s_label, t_label, kernel_mul = 2.0, kernel_num = 5, fix_sigma=None):
    s_label = s_label.cpu()
    t_label = t_label.cpu()
    batch_size_s = int(s_label.size()[0])
    batch_size_t = int(t_label.size()[0])
    batch_size = min(batch_size_s, batch_size_t)
 
    s_label = s_label[:batch_size]
    t_label = t_label[:batch_size]
    source = source[:batch_size]
    target = target[:batch_size]    
    
    s_label = s_label.view(batch_size,1)
    s_label = torch.zeros(batch_size, 31).scatter_(1, s_label.data, 1)
    s_label = Variable(s_label, requires_grad=True).cuda()  
    
    t_label = t_label.view(batch_size,1)
    t_label = torch.zeros(batch_size,31).scatter_(1, t_label.data, 1)
    t_label = Variable(t_label, requires_grad=True).cuda()  
    
    kernels = guassian_kernel(source, target, kernel_mul=kernel_mul, kernel_num=kernel_num, fix_sigma=fix_sigma)
    loss = 0
    XX = kernels[:batch_size, :batch_size]   
    YY = kernels[batch_size:, batch_size:]   
    XY = kernels[:batch_size, batch_size:]       
    
    loss += torch.mean(torch.mm(s_label, torch.transpose(s_label, 0, 1)) ** XX +
                      torch.mm(t_label, torch.transpose(t_label, 0, 1)) ** YY - 
                      2 * torch.mm(s_label, torch.transpose(t_label, 0, 1)) ** XY)
    
    return loss