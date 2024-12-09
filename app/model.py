import torch
import torch.nn as nn
import torch.nn.functional as F

class DoubleConv(nn.Module):
    """
    兩個連續的卷積層，每個卷積層後面跟著 Batch Normalization 和 ReLU 激活。

    Attributes:
        double_conv (nn.Sequential): 包含卷積層、批量歸一化和 ReLU 的序列容器。
    """

    def __init__(self, in_channels: int, out_channels: int) -> None:
        """
        初始化 DoubleConv 模塊。

        Args:
            in_channels (int): 輸入通道數。
            out_channels (int): 輸出通道數。
        """
        super(DoubleConv, self).__init__()
        self.double_conv: nn.Sequential = nn.Sequential(
            nn.Conv2d(in_channels, out_channels, kernel_size=3, padding=1),
            nn.BatchNorm2d(out_channels),  
            nn.ReLU(inplace=True),
            nn.Conv2d(out_channels, out_channels, kernel_size=3, padding=1),
            nn.BatchNorm2d(out_channels),  
            nn.ReLU(inplace=True),
        )
        
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        DoubleConv 模塊的前向傳播。

        Args:
            x (torch.Tensor): 輸入張量，形狀為 (batch_size, in_channels, H, W)。

        Returns:
            torch.Tensor: 輸出張量，形狀為 (batch_size, out_channels, H, W)。
        """
        return self.double_conv(x)

class UNet3Plus(nn.Module):
    """
    U-Net3+ 用於圖像分割，基於多層特徵融合的改進版本。

    Attributes:
        inconv (DoubleConv): 初始卷積模塊。
        down1, down2, down3, down4 (nn.Sequential): 下採樣模塊，包含最大池化和 DoubleConv。
        up1, up2, up3, up4 (nn.ConvTranspose2d): 上採樣層，使用轉置卷積進行上採樣。
        conv1, conv2, conv3, conv4 (DoubleConv): 與多層特徵拼接後的卷積層。
        outconv (nn.Conv2d): 最終輸出卷積層，用於生成分割圖。
    """

    def __init__(self, n_channels: int = 3, n_classes: int = 1, base_channels: int = 64) -> None:
        """
        初始化 U-Net3+ 模型。

        Args:
            n_channels (int, optional): 輸入通道數，默認為 3（RGB 圖像）。
            n_classes (int, optional): 分割的類別數，默認為 1（二元分割）。
            base_channels (int, optional): 基礎通道數，默認為 64。
        """
        super(UNet3Plus, self).__init__()
        
        # 下採樣路徑
        self.inconv: DoubleConv = DoubleConv(n_channels, base_channels)
        self.down1: nn.Sequential = nn.Sequential(nn.MaxPool2d(2), DoubleConv(base_channels, base_channels * 2))
        self.down2: nn.Sequential = nn.Sequential(nn.MaxPool2d(2), DoubleConv(base_channels * 2, base_channels * 4))
        self.down3: nn.Sequential = nn.Sequential(nn.MaxPool2d(2), DoubleConv(base_channels * 4, base_channels * 8))
        self.down4: nn.Sequential = nn.Sequential(nn.MaxPool2d(2), DoubleConv(base_channels * 8, base_channels * 16))
        
        # 上採樣路徑與多層特徵融合
        self.up1: nn.ConvTranspose2d = nn.ConvTranspose2d(base_channels * 16, base_channels * 8, kernel_size=2, stride=2)
        self.conv1: DoubleConv = DoubleConv(
            base_channels * 8 + base_channels * 8 + base_channels * 4 + base_channels * 2 + base_channels, 
            base_channels * 8
        )
        
        self.up2: nn.ConvTranspose2d = nn.ConvTranspose2d(base_channels * 8, base_channels * 4, kernel_size=2, stride=2)
        self.conv2: DoubleConv = DoubleConv(
            base_channels * 4 + base_channels * 4 + base_channels * 2 + base_channels, 
            base_channels * 4
        )
        
        self.up3: nn.ConvTranspose2d = nn.ConvTranspose2d(base_channels * 4, base_channels * 2, kernel_size=2, stride=2)
        self.conv3: DoubleConv = DoubleConv(
            base_channels * 2 + base_channels * 2 + base_channels, 
            base_channels * 2
        )
        
        self.up4: nn.ConvTranspose2d = nn.ConvTranspose2d(base_channels * 2, base_channels, kernel_size=2, stride=2)
        self.conv4: DoubleConv = DoubleConv(
            base_channels + base_channels,  # 修改後：64 + 64 = 128
            base_channels
        )
        
        # 輸出層
        self.outconv: nn.Conv2d = nn.Conv2d(base_channels, n_classes, kernel_size=1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        定義 U-Net3+ 模型的前向傳播。

        Args:
            x (torch.Tensor): 輸入張量，形狀為 (batch_size, n_channels, H, W)。

        Returns:
            torch.Tensor: 輸出張量，形狀為 (batch_size, n_classes, H, W)。
        """
        # 下採樣路徑
        x1: torch.Tensor = self.inconv(x)    # [batch_size, base_channels, H, W]
        x2: torch.Tensor = self.down1(x1)    # [batch_size, base_channels*2, H/2, W/2]
        x3: torch.Tensor = self.down2(x2)    # [batch_size, base_channels*4, H/4, W/4]
        x4: torch.Tensor = self.down3(x3)    # [batch_size, base_channels*8, H/8, W/8]
        x5: torch.Tensor = self.down4(x4)    # [batch_size, base_channels*16, H/16, W/16]

        # 上採樣路徑與多層特徵融合

        # 上採樣階段 1
        up1: torch.Tensor = self.up1(x5)                             # [batch_size, base_channels*8, H/8, W/8]
        up1_interp_x3: torch.Tensor = F.interpolate(
            x3, size=up1.size()[2:], mode='bilinear', align_corners=True
        )  # [batch_size, base_channels*4, H/8, W/8]
        up1_interp_x2: torch.Tensor = F.interpolate(
            x2, size=up1.size()[2:], mode='bilinear', align_corners=True
        )  # [batch_size, base_channels*2, H/8, W/8]
        up1_interp_x1: torch.Tensor = F.interpolate(
            x1, size=up1.size()[2:], mode='bilinear', align_corners=True
        )  # [batch_size, base_channels, H/8, W/8]
        
        up1_cat: torch.Tensor = torch.cat([up1, x4, up1_interp_x3, up1_interp_x2, up1_interp_x1], dim=1)
        up1: torch.Tensor = self.conv1(up1_cat)                       # [batch_size, base_channels*8, H/8, W/8]

        # 上採樣階段 2
        up2: torch.Tensor = self.up2(up1)                             # [batch_size, base_channels*4, H/4, W/4]
        up2_interp_x2: torch.Tensor = F.interpolate(
            x2, size=up2.size()[2:], mode='bilinear', align_corners=True
        )  # [batch_size, base_channels*2, H/4, W/4]
        up2_interp_x1: torch.Tensor = F.interpolate(
            x1, size=up2.size()[2:], mode='bilinear', align_corners=True
        )  # [batch_size, base_channels, H/4, W/4]
        
        up2_cat: torch.Tensor = torch.cat([up2, x3, up2_interp_x2, up2_interp_x1], dim=1)
        up2: torch.Tensor = self.conv2(up2_cat)                       # [batch_size, base_channels*4, H/4, W/4]

        # 上採樣階段 3
        up3: torch.Tensor = self.up3(up2)                             # [batch_size, base_channels*2, H/2, W/2]
        up3_interp_x1: torch.Tensor = F.interpolate(
            x1, size=up3.size()[2:], mode='bilinear', align_corners=True
        )  # [batch_size, base_channels, H/2, W/2]
        
        up3_cat: torch.Tensor = torch.cat([up3, x2, up3_interp_x1], dim=1)
        up3: torch.Tensor = self.conv3(up3_cat)                       # [batch_size, base_channels*2, H/2, W/2]

        # 上採樣階段 4
        up4: torch.Tensor = self.up4(up3)                             # [batch_size, base_channels, H, W]
        up4_cat: torch.Tensor = torch.cat([up4, x1], dim=1)
        up4: torch.Tensor = self.conv4(up4_cat)                       # [batch_size, base_channels, H, W]

        # 輸出層
        out: torch.Tensor = self.outconv(up4)                          # [batch_size, n_classes, H, W]
        return out